# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import io
import json
import logging
import os
import threading
from collections import defaultdict
from collections.abc import Generator
from dataclasses import dataclass
from functools import cached_property
from time import time
from typing import cast

import cv2
import numpy as np
from model_api.adapters import OpenvinoAdapter, create_core
from model_api.models.sam_models import SAMDecoder, SAMImageEncoder
from model_api.models.visual_prompting import SAMLearnableVisualPrompter, ZSLVisualPromptingResult

from entities.reference_feature import ReferenceFeature, ReferenceMediaInfo
from repos.reference_feature_repo import ReferenceFeatureRepo
from repos.vps_dataset_filter_repo import VPSDatasetFilterRepo
from services.converters import AnnotationConverter, PromptConverter, VisualPromptingFeaturesConverter
from services.exceptions import ImageNotFoundException, VideoNotFoundException
from services.readme import PROMPT_MODEL_README

from geti_fastapi_tools.exceptions import InvalidMediaException
from geti_types import (
    ID,
    DatasetStorageIdentifier,
    MediaIdentifierEntity,
    MediaType,
    ProjectIdentifier,
    VideoFrameIdentifier,
)
from iai_core.adapters.binary_interpreters import RAWBinaryInterpreter
from iai_core.algorithms import ModelTemplateList
from iai_core.algorithms.visual_prompting import VISUAL_PROMPTING_MODEL_TEMPLATE_ID
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.entities.annotation import Annotation
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.evaluation_result import EvaluationPurpose, EvaluationResult, NullEvaluationResult
from iai_core.entities.image import Image, NullImage
from iai_core.entities.label import Domain
from iai_core.entities.metrics import MultiScorePerformance, ScoreMetric
from iai_core.entities.model import (
    Model,
    ModelConfiguration,
    ModelFormat,
    NullModel,
    TrainingFramework,
    TrainingFrameworkType,
)
from iai_core.entities.model_storage import ModelStorage, NullModelStorage
from iai_core.entities.model_template import NullModelTemplate
from iai_core.entities.scored_label import LabelSource, ScoredLabel
from iai_core.entities.shapes import Rectangle
from iai_core.entities.subset import Subset
from iai_core.entities.video import NullVideo, VideoFrame
from iai_core.repos import (
    AnnotationSceneRepo,
    DatasetRepo,
    EvaluationResultRepo,
    ImageRepo,
    LabelSchemaRepo,
    ModelRepo,
    ModelStorageRepo,
    ProjectRepo,
    VideoRepo,
)
from iai_core.repos.storage.s3_connector import S3Connector
from media_utils import get_media_numpy

SAM_ENCODER_XML_PATH_ENV = "SAM_ENCODER_XML_PATH"
SAM_ENCODER_BIN_PATH_ENV = "SAM_ENCODER_BIN_PATH"
SAM_DECODER_XML_PATH_ENV = "SAM_DECODER_XML_PATH"
SAM_DECODER_BIN_PATH_ENV = "SAM_DECODER_BIN_PATH"
PERFORMANCE_HINT = "LATENCY"
SUPPORTED_LABEL_DOMAINS = {
    Domain.DETECTION,
    Domain.ROTATED_DETECTION,
    Domain.SEGMENTATION,
    Domain.INSTANCE_SEGMENTATION,
}
SAM_ENCODER_XML_KEY = "encoder.xml"
SAM_ENCODER_BIN_KEY = "encoder.bin"
SAM_DECODER_XML_KEY = "decoder.xml"
SAM_DECODER_BIN_KEY = "decoder.bin"
README_FILE_KEY = "README.md"
REFERENCE_FEATURES_JSON = "reference_features.json"
DICE_INTERSECTION = "dice_intersection"
DICE_CARDINALITY = "dice_cardinality"
RESIZED_IMAGE_SIZE = 800  # fixed pixel dimensions for the resized image

logger = logging.getLogger(__name__)

lock = threading.RLock()


@dataclass(frozen=True)
class VPSPredictionResults:
    """
    Prediction results from visual prompting.

    :param bboxes: list of predicted bounding boxes
    :param rotated_bboxes: list of predicted rotated bounding boxes
    :param polygons: list of predicted polygons
    """

    bboxes: list[Annotation]
    rotated_bboxes: list[Annotation]
    polygons: list[Annotation]


class VisualPromptService:
    """
    VisualPromptService provides methods for visual prompting inference and one-shot-learning.

    :param device: device to run inference on. Defaults to CPU.
    :param max_async_requests: maximum number of asynchronous requests to be used for inference.
        Defaults to 0, equivalent to number of cores available.
    :param visual_prompter_model: SAMLearnableVisualPrompter model to be used for inference.
        If None, the model is loaded from S3.
    """

    pretrained_weights_bucket_name: str = os.getenv("BUCKET_NAME_PRETRAINEDWEIGHTS", "pretrainedweights")

    def __init__(
        self,
        device: str = "CPU",
        max_async_requests: int = 0,
        visual_prompter_model: SAMLearnableVisualPrompter | None = None,
    ) -> None:
        self._openvino_core = create_core()
        self._device = device
        self._max_async_requests = max_async_requests
        self.s3_client, _ = S3Connector.get_clients()
        self._sam_encoder_xml_path = os.getenv(SAM_ENCODER_XML_PATH_ENV)
        self._sam_encoder_bin_path = os.getenv(SAM_ENCODER_BIN_PATH_ENV)
        self._sam_decoder_xml_path = os.getenv(SAM_DECODER_XML_PATH_ENV)
        self._sam_decoder_bin_path = os.getenv(SAM_DECODER_BIN_PATH_ENV)
        if visual_prompter_model:
            self.visual_prompter_model = visual_prompter_model
        else:
            self.visual_prompter_model = SAMLearnableVisualPrompter(
                encoder_model=self._load_sam_encoder(),
                decoder_model=self._load_sam_mask_decoder(),
            )

    def infer(
        self,
        project_identifier: ProjectIdentifier,
        task_id: ID,
        media: np.ndarray,
    ) -> VPSPredictionResults:
        """
        Run inference on the given media and return predicted annotations.

        :param project_identifier: project identifier
        :param task_id: The task ID for which predictions are to be made.
        :param media: The media (image or video frame or raw numpy array) for which predictions are to be made.
            The media is expected to be an RGB array of shape (Height, Width, Channels) with uint8 type (0-255).
        :param roi: The region of interest (ROI) to be used for inference. Defaults to None.
        :return: list of predicted annotations
        """
        # Stage 1: check reference features and apply one-shot-learning for missing labels
        reference_features_repo = ReferenceFeatureRepo(project_identifier)
        learned_label_ids = set(reference_features_repo.get_all_ids_by_task_id(task_id=task_id))
        label_schema = LabelSchemaRepo(project_identifier).get_latest_view_by_task(task_node_id=task_id)
        compatible_labels_by_id = {
            label.id_: label
            for label in label_schema.get_all_labels()
            if label.domain in SUPPORTED_LABEL_DOMAINS and not label.is_empty
        }
        compatible_label_ids = set(compatible_labels_by_id.keys())
        missing_labels = compatible_label_ids - learned_label_ids

        if missing_labels:
            self.one_shot_learn(
                project_identifier=project_identifier,
                label_ids=list(missing_labels),
                task_id=task_id,
            )

        # Stage 2: fetch latest reference features and infer on media
        reference_features = reference_features_repo.get_all_by_task_id(task_id=task_id)
        # add full box rectangle annotation with empty label if no predictions are made
        empty_label = label_schema.get_empty_labels()[0]
        empty_annotation = Annotation(
            shape=Rectangle.generate_full_box(),
            labels=[ScoredLabel(label_id=empty_label.id_, is_empty=True, probability=1.0)],
        )

        if not reference_features:
            logger.warning(
                "No reference features found for project with ID `%s`. Returning empty predictions.",
                project_identifier.project_id,
            )
            return VPSPredictionResults(bboxes=[empty_annotation], rotated_bboxes=[], polygons=[])

        logger.debug(
            "Retrieved reference features for project with ID `%s`: %s",
            project_identifier.project_id,
            reference_features,
        )

        # conversion to ModelAPI input format
        feature_converter = VisualPromptingFeaturesConverter(list(compatible_labels_by_id.keys()))
        visual_prompting_features = feature_converter.convert_to_visual_prompting_features(
            reference_features=reference_features
        )
        resized_image = self._resize_image(media)
        with lock:
            visual_prompting_result = self.visual_prompter_model.infer(
                image=resized_image,
                reference_features=visual_prompting_features,
                apply_masks_refinement=False,
            )

        # Stage 3: convert ModelAPI predicted segmentation masks to annotations
        model_storage = self._get_or_create_sam_model_storage(project_identifier=project_identifier, task_id=task_id)
        model = ModelRepo(model_storage.identifier).get_one()
        label_source = LabelSource(model_id=model.id_, model_storage_id=model_storage.id_)
        predicted_bboxes = []
        predicted_rotated_bboxes = []
        predicted_polygons = []
        for label_index, predicted_mask in visual_prompting_result.data.items():
            label_id = feature_converter.index_to_label_id(label_index)
            label = compatible_labels_by_id[label_id]
            match label.domain:
                case Domain.DETECTION:
                    predicted_bboxes += AnnotationConverter.convert_to_bboxes(
                        predicted_mask=predicted_mask,
                        predicted_label=label,
                        label_source=label_source,
                    )
                case Domain.ROTATED_DETECTION:
                    predicted_rotated_bboxes += AnnotationConverter.convert_to_rotated_bboxes(
                        predicted_mask=predicted_mask,
                        predicted_label=label,
                        label_source=label_source,
                    )
                case Domain.SEGMENTATION | Domain.INSTANCE_SEGMENTATION:
                    predicted_polygons += AnnotationConverter.convert_to_polygons(
                        predicted_mask=predicted_mask,
                        predicted_label=label,
                        label_source=label_source,
                    )
                case _:
                    raise ValueError(
                        f"Visual prompting contains results for unsupported label with ID `{label_id}` "
                        f"and domain `{label.domain}`."
                    )
        if not predicted_bboxes and not predicted_rotated_bboxes and not predicted_polygons:
            predicted_bboxes.append(empty_annotation)
        return VPSPredictionResults(
            bboxes=predicted_bboxes,
            rotated_bboxes=predicted_rotated_bboxes,
            polygons=predicted_polygons,
        )

    @staticmethod
    def _get_2d_media_by_media_identifier(
        dataset_storage_identifier: DatasetStorageIdentifier,
        media_identifier: MediaIdentifierEntity,
    ) -> tuple[Image | VideoFrame, np.ndarray]:
        """
        Get a 2D media (Image or VideoFrame) from a media identifier.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the media
        :param media_identifier: Media identifier
        :return: Image or VideoFrame
        """
        media: Image | VideoFrame
        if media_identifier.media_type == MediaType.IMAGE:
            image = ImageRepo(dataset_storage_identifier).get_by_id(media_identifier.media_id)
            if image is None or isinstance(image, NullImage):
                raise ImageNotFoundException(
                    image_id=media_identifier.media_id,
                    dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
                )
            media = image
        elif isinstance(media_identifier, VideoFrameIdentifier):
            video = VideoRepo(dataset_storage_identifier).get_by_id(media_identifier.media_id)
            if video is None or isinstance(video, NullVideo):
                raise VideoNotFoundException(
                    video_id=media_identifier.media_id,
                    dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
                )
            media = VideoFrame(video=video, frame_index=media_identifier.frame_index)
        else:
            raise InvalidMediaException(
                f"Cannot get media for type `{media_identifier.media_type}`. "
                f"Only `IMAGE` and `VIDEO_FRAME` are supported."
            )
        return media, get_media_numpy(dataset_storage_identifier=dataset_storage_identifier, media=media)

    def one_shot_learn(
        self, project_identifier: ProjectIdentifier, label_ids: list[ID], task_id: ID
    ) -> list[ReferenceFeature]:
        """
        Apply one-shot-learning for the given label IDs and save the reference features.

        :param project_identifier: project identifier
        :param label_ids: list of label IDs to learn
        :param task_id: task ID for which the labels are to be learned
        :return: list of reference features
        """
        start_time = time()
        annotation_filter_repo = VPSDatasetFilterRepo(project_identifier)
        # TODO remove limitation of sampling only from the training dataset storage
        training_dataset_storage_id = ProjectRepo().get_by_id(project_identifier.project_id).training_dataset_storage_id
        sampling_results = list(
            annotation_filter_repo.sample_annotations_by_label_ids(
                label_ids=label_ids, dataset_storage_id=training_dataset_storage_id
            )
        )
        if not sampling_results:
            logger.info(f"No annotations found for label_ids {label_ids}. Skipping one-shot learn.")
            return []
        logger.info(f"One-shot learn on label_ids {label_ids}, # of samples: {len(sampling_results)}")

        reference_features = []
        prompt_converter = PromptConverter(label_ids=label_ids)
        feature_converter = VisualPromptingFeaturesConverter(label_ids=label_ids)
        dice_intersection_per_label: dict[ID, int] = defaultdict(int)
        dice_cardinality_per_label: dict[ID, int] = defaultdict(int)
        dataset_items = []
        for sample_result in sampling_results:
            annotation_scene = AnnotationSceneRepo(sample_result.dataset_storage_identifier).get_by_id(
                sample_result.annotation_scene_id
            )
            media, numpy_data = VisualPromptService._get_2d_media_by_media_identifier(
                dataset_storage_identifier=sample_result.dataset_storage_identifier,
                media_identifier=annotation_scene.media_identifier,
            )
            reference_dataset_item = DatasetItem(
                id_=DatasetRepo.generate_id(),
                media=media,
                annotation_scene=annotation_scene,
                subset=Subset.TRAINING,
            )
            dataset_items.append(reference_dataset_item)

            resized_image = self._resize_image(numpy_data)
            image_height = resized_image.shape[0]
            image_width = resized_image.shape[1]
            bbox_prompts = prompt_converter.extract_bbox_prompts(
                annotation_scene=annotation_scene,
                height=image_height,
                width=image_width,
            )
            polygon_prompts = prompt_converter.extract_polygon_prompts(
                annotation_scene=annotation_scene,
                height=image_height,
                width=image_width,
            )

            with lock:
                visual_prompting_features, masks = self.visual_prompter_model.learn(
                    image=resized_image,
                    boxes=bbox_prompts,
                    polygons=polygon_prompts,
                    reset_features=True,
                )
            ref_features = feature_converter.convert_to_reference_features(
                visual_prompting_features=visual_prompting_features,
                reference_media_info=ReferenceMediaInfo(
                    dataset_storage_id=sample_result.dataset_storage_identifier.dataset_storage_id,
                    annotation_scene_id=sample_result.annotation_scene_id,
                    media_identifier=annotation_scene.media_identifier,
                ),
                task_id=task_id,
            )

            with lock:
                results = self.visual_prompter_model.infer(
                    image=resized_image,
                    reference_features=visual_prompting_features,
                    apply_masks_refinement=False,
                )
            dice_generator = self._generate_intersection_and_cardinalities(
                image_height=resized_image.shape[0],
                image_width=resized_image.shape[1],
                reference_masks=masks,
                visual_prompting_result=results,
            )
            for label_idx, intersection, cardinality in dice_generator:
                label_id = feature_converter.index_to_label_id(label_idx)
                dice_intersection_per_label[label_id] += intersection
                dice_cardinality_per_label[label_id] += cardinality

            reference_features += ref_features
        duration = time() - start_time
        ReferenceFeatureRepo(project_identifier).save_many(reference_features)
        self._save_sam_model(
            project_identifier=project_identifier,
            task_id=task_id,
            reference_features=reference_features,
            learning_duration=duration,
            dataset_items=dataset_items,
            dice_intersection_per_label=dice_intersection_per_label,
            dice_cardinality_per_label=dice_cardinality_per_label,
        )
        return reference_features

    def _load_bytes_from_s3(self, filename: str | None) -> bytes:
        if filename is None:
            raise ValueError("Cannot load file from S3. Filename is not provided.")
        obj = self.s3_client.get_object(
            bucket_name=VisualPromptService.pretrained_weights_bucket_name,
            object_name=filename,
        )
        return RAWBinaryInterpreter().interpret(io.BytesIO(obj.data), filename=filename)

    @cached_property
    def _sam_encoder_xml(self) -> bytes:
        return self._load_bytes_from_s3(self._sam_encoder_xml_path)

    @cached_property
    def _sam_encoder_bin(self) -> bytes:
        return self._load_bytes_from_s3(self._sam_encoder_bin_path)

    @cached_property
    def _sam_decoder_xml(self) -> bytes:
        return self._load_bytes_from_s3(self._sam_decoder_xml_path)

    @cached_property
    def _sam_decoder_bin(self) -> bytes:
        return self._load_bytes_from_s3(self._sam_decoder_bin_path)

    def _load_sam_encoder(self) -> SAMImageEncoder:
        if self._sam_encoder_xml_path is None or self._sam_encoder_bin_path is None:
            raise ValueError("Cannot load SAM encoder. Please make sure the correct environment variables are set.")

        encoder_adapter = OpenvinoAdapter(
            self._openvino_core,
            model=self._sam_encoder_xml,
            weights_path=self._sam_encoder_bin,
            device=self._device,
            max_num_requests=self._max_async_requests,
            plugin_config={"PERFORMANCE_HINT": PERFORMANCE_HINT},
        )
        logger.info("SAM encoder loaded successfully.")
        return SAMImageEncoder(
            inference_adapter=encoder_adapter,
            preload=True,
        )

    def _load_sam_mask_decoder(self) -> SAMDecoder:
        if self._sam_decoder_xml_path is None or self._sam_decoder_bin_path is None:
            raise ValueError("Cannot load SAM decoder. Please make sure the correct environment variables are set.")

        decoder_adapter = OpenvinoAdapter(
            self._openvino_core,
            model=self._sam_decoder_xml,
            weights_path=self._sam_decoder_bin,
            device=self._device,
            max_num_requests=self._max_async_requests,
            plugin_config={"PERFORMANCE_HINT": PERFORMANCE_HINT},
        )
        logger.info("SAM decoder loaded successfully.")
        return SAMDecoder(
            model_adapter=decoder_adapter,
            preload=True,
        )

    def _save_sam_model(
        self,
        project_identifier: ProjectIdentifier,
        task_id: ID,
        reference_features: list[ReferenceFeature],
        learning_duration: float,
        dataset_items: list[DatasetItem],
        dice_intersection_per_label: dict[ID, int],
        dice_cardinality_per_label: dict[ID, int],
    ) -> None:
        """
        Save SAM model with reference features. The following data sources are saved:
            - "encoder.xml"
            - "encoder.bin"
            - "decoder.xml"
            - "decoder.bin"
            - "reference_features.json": containing information about the labels associated with the reference features.
            - "{label_id}.npz": containing the numpy array of the reference feature.

        :param project_identifier: project in which the SAM model is to be saved
        :param task_id: task ID for which the SAM model is to be saved
        :param reference_features: list of reference features learned for the SAM model
        :param learning_duration: one shot learning duration in seconds
        :param dataset_items: list of dataset items used for one-shot-learning
        :param dice_intersection_per_label: Dice metric pixel-wise intersection for each label
        :param dice_cardinality_per_label: Dice metric cardinality for each label
        """
        project = ProjectRepo().get_by_id(project_identifier.project_id)
        sam_model_storage = self._get_or_create_sam_model_storage(
            project_identifier=project_identifier, task_id=task_id
        )
        model_repo = ModelRepo(sam_model_storage.identifier)
        label_schema = LabelSchemaRepo(project_identifier).get_latest_view_by_task(task_node_id=task_id)
        label_map = label_schema.get_label_map()
        sam = model_repo.get_one()

        # create new SAM model if not found
        configuration = ModelConfiguration(
            configurable_parameters=ConfigurableParameters(header="Default parameters", visible_in_ui=False),
            label_schema=label_schema,
        )
        reference_dataset: Dataset
        ds_identifier = project.get_training_dataset_storage().identifier
        if isinstance(sam, NullModel):
            logger.info(
                "No SAM model found for task ID `%s`; creating one with a new reference dataset.",
                task_id,
            )
            reference_dataset = Dataset(
                id=DatasetRepo.generate_id(),
                items=dataset_items,
                purpose=DatasetPurpose.TRAINING,
                label_schema_id=label_schema.id_,
            )
            model_data_sources = {
                SAM_ENCODER_XML_KEY: self._sam_encoder_xml,
                SAM_ENCODER_BIN_KEY: self._sam_encoder_bin,
                SAM_DECODER_XML_KEY: self._sam_decoder_xml,
                SAM_DECODER_BIN_KEY: self._sam_decoder_bin,
                README_FILE_KEY: PROMPT_MODEL_README.encode(),
            }
            sam = Model(
                project=project,
                model_storage=sam_model_storage,
                train_dataset=reference_dataset,
                configuration=configuration,
                id_=model_repo.generate_id(),
                data_source_dict=model_data_sources,
                training_framework=TrainingFramework(
                    type=TrainingFrameworkType.GETI_VPS,
                    version="1.0",
                ),
                model_format=ModelFormat.OPENVINO,
                training_duration=learning_duration,
            )
        else:
            logger.info(
                "SAM model already exists for task ID `%s`; updating its reference dataset.",
                task_id,
            )
            # Update model's label schema and dataset
            # The new reference dataset keeps the id of the old one (to avoid breaking references from other entities)
            # but it also includes the new dataset items.
            old_reference_dataset = sam.get_train_dataset()
            reference_dataset = Dataset(
                id=old_reference_dataset.id_,
                items=old_reference_dataset._items + dataset_items,
                purpose=DatasetPurpose.TRAINING,
                label_schema_id=label_schema.id_,
                creation_date=old_reference_dataset.creation_date,
            )
            sam.train_dataset = reference_dataset
            sam.configuration = configuration
        DatasetRepo(ds_identifier).save_deep(reference_dataset)

        reference_feature_dict = {}
        existing_ref_feat_adapter = sam.model_adapters.get(REFERENCE_FEATURES_JSON)
        if existing_ref_feat_adapter is not None:
            reference_feature_dict = json.loads(existing_ref_feat_adapter.data)

        # save with unique filename: "reference_feature_{offset}.npz"
        idx_offset = 1
        for ref_feat in reference_features:
            label = label_map[ref_feat.label_id]
            while (numpy_filename := f"reference_feature_{idx_offset}.npz") in sam.model_adapters:
                idx_offset += 1
            sam.set_data(key=numpy_filename, data=ref_feat.numpy_npz_bytes)
            reference_feature_dict[ref_feat.label_id] = {
                "label_id": ref_feat.label_id,
                "name": label.name,
                "color": label.color.hex_str,
                "numpy_filename": numpy_filename,
            }

        sam.set_data(
            key=REFERENCE_FEATURES_JSON,
            data=json.dumps(reference_feature_dict, indent=4).encode(),
        )
        ModelRepo(sam_model_storage.identifier).save(sam)

        logger.info(f"Saved SAM model with ID `{sam.id_}`.")

        self._save_sam_evaluation_result(
            project_identifier=project_identifier,
            model=sam,
            dataset_storage_identifier=ds_identifier,
            dataset=reference_dataset,
            dice_intersection_per_label=dice_intersection_per_label,
            dice_cardinality_per_label=dice_cardinality_per_label,
        )

    @staticmethod
    def _get_or_create_sam_model_storage(project_identifier: ProjectIdentifier, task_id: ID) -> ModelStorage:
        model_storage_repo = ModelStorageRepo(project_identifier)
        sam_model_storage = model_storage_repo.get_one_by_task_node_id(
            task_node_id=task_id,
            extra_filter={
                "model_template_id": VISUAL_PROMPTING_MODEL_TEMPLATE_ID,
            },
        )
        if not isinstance(sam_model_storage, NullModelStorage):
            return sam_model_storage

        model_template = ModelTemplateList().get_by_id(VISUAL_PROMPTING_MODEL_TEMPLATE_ID)
        if isinstance(model_template, NullModelTemplate):
            error_msg = f"Could not find `{VISUAL_PROMPTING_MODEL_TEMPLATE_ID}` model template."
            logger.exception(error_msg)
            raise ValueError(error_msg)

        sam_model_storage = ModelStorage(
            id_=model_storage_repo.generate_id(),
            project_id=project_identifier.project_id,
            task_node_id=task_id,
            model_template=model_template,
        )
        model_storage_repo.save(sam_model_storage)
        return sam_model_storage

    @staticmethod
    def _generate_intersection_and_cardinalities(
        image_height: int,
        image_width: int,
        reference_masks: np.ndarray,
        visual_prompting_result: ZSLVisualPromptingResult,
    ) -> Generator[tuple[int, int, int], None, None]:
        """
        Return a generator that yields the pixel-wise intersection and the cardinality (total number of pixels)
        for each pair of reference and predicted segmentation masks.

        :param image_height: height of the image
        :param image_width: width of the image
        :param reference_masks: the reference segmentation masks
        :param visual_prompting_result: visual prompting result in ModelAPI format
        :return: generator with label ID, pixel intersection, and cardinality
        """
        for label_idx, predicted_mask in visual_prompting_result.data.items():
            if label_idx >= len(reference_masks):
                logger.warning(
                    f"Inference results contain label index `{label_idx}` with a mask of shape "
                    f"{predicted_mask.mask.shape}, but no corresponding reference mask is found "
                    f"(shape: {reference_masks.shape})."
                )
                continue
            ref_mask = reference_masks[label_idx]
            # each object has a separate mask, so we need to combine them
            pred_mask = np.zeros((image_height, image_width), dtype=np.uint8)
            for obj_mask in predicted_mask.mask:
                pred_mask = pred_mask | obj_mask
            intersection = np.count_nonzero(np.where(ref_mask == pred_mask, ref_mask, 0))
            cardinality = np.count_nonzero(ref_mask) + np.count_nonzero(pred_mask)
            yield label_idx, intersection, cardinality

    @staticmethod
    def _save_sam_evaluation_result(
        project_identifier: ProjectIdentifier,
        model: Model,
        dataset_storage_identifier: DatasetStorageIdentifier,
        dataset: Dataset,
        dice_intersection_per_label: dict[ID, int],
        dice_cardinality_per_label: dict[ID, int],
    ) -> None:
        """
        Computes the overall Dice score and saves the evaluation result for the SAM model.

        :param project_identifier: project identifier
        :param model: SAM model
        :param dataset_storage_identifier: dataset storage identifier
        :param dataset: dataset used for evaluation
        :param dice_intersection_per_label: pixel-wise intersection for each label
        :param dice_cardinality_per_label: cardinality for each label
        """
        evaluation_result_repo = EvaluationResultRepo(project_identifier)
        evaluation_result = evaluation_result_repo.get_latest_by_model_ids([model.id_])
        if isinstance(evaluation_result, NullEvaluationResult):
            evaluation_result = EvaluationResult(
                id_=EvaluationResultRepo.generate_id(),
                project_identifier=project_identifier,
                dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
                model_storage_id=model.model_storage.id_,
                model_id=model.id_,
                ground_truth_dataset=dataset,
                prediction_dataset=dataset,
                purpose=EvaluationPurpose.TEST,
            )
        performance = evaluation_result.performance if evaluation_result.has_score_metric() else MultiScorePerformance()
        performance = cast("MultiScorePerformance", performance)

        # get existing intersection and cardinality scores
        intersection_score_metric_per_label = {}
        cardinality_score_metric_per_label = {}
        for score in performance.additional_scores:
            if score.name == DICE_INTERSECTION:
                intersection_score_metric_per_label[score.label_id] = score
            elif score.name == DICE_CARDINALITY:
                cardinality_score_metric_per_label[score.label_id] = score

        # compute overall Dice score and update score metrics
        overall_intersection = 0
        overall_cardinality = 0
        labels = model.get_label_schema().get_labels(include_empty=False)
        default_score_metric = ScoreMetric(name="", value=0.0)
        performance.additional_scores = []  # reset scores
        for label in labels:
            existing_intersection_val = intersection_score_metric_per_label.get(label.id_, default_score_metric).value
            existing_cardinality_val = cardinality_score_metric_per_label.get(label.id_, default_score_metric).value
            overall_intersection += int(abs(dice_intersection_per_label.get(label.id_, 0) - existing_intersection_val))
            overall_cardinality += int(abs(dice_cardinality_per_label.get(label.id_, 0) - existing_cardinality_val))
            # replace existing score metrics with new values
            if label.id_ in dice_intersection_per_label:
                intersection_score_metric_per_label[label.id_] = ScoreMetric(
                    label_id=label.id_,
                    name=DICE_INTERSECTION,
                    value=dice_intersection_per_label[label.id_],
                )
            if label.id_ in dice_cardinality_per_label:
                cardinality_score_metric_per_label[label.id_] = ScoreMetric(
                    label_id=label.id_,
                    name=DICE_CARDINALITY,
                    value=dice_cardinality_per_label[label.id_],
                )
            if label.id_ in intersection_score_metric_per_label and label.id_ in cardinality_score_metric_per_label:
                performance.add_score(intersection_score_metric_per_label[label.id_])
                performance.add_score(cardinality_score_metric_per_label[label.id_])

        overall_dice_score = 2 * overall_intersection / overall_cardinality if overall_cardinality else 0
        performance.primary_score = ScoreMetric(name="Dice", value=overall_dice_score)

        evaluation_result.performance = performance
        evaluation_result_repo.save(evaluation_result)
        logger.info(f"Saved evaluation result for model `{model.id_}` with score `{overall_dice_score}`.")

    @staticmethod
    def _resize_image(image: np.ndarray) -> np.ndarray:
        """
        Resize the image while maintaining the aspect ratio. If the image is already smaller than the target size,
        no resizing is performed.

        :param image: input image
        :return: resized image
        """
        og_height, og_width = image.shape[:2]
        # resize the largest dimension to RESIZED_IMAGE_SIZE while maintaining the aspect ratio
        if og_height > og_width:
            new_height = RESIZED_IMAGE_SIZE
            new_width = int(new_height / og_height * og_width)
        else:
            new_width = RESIZED_IMAGE_SIZE
            new_height = int(new_width / og_width * og_height)
        if og_height * og_width > new_height * new_width:
            # AREA interpolation works best when downscaling:
            # https://web.archive.org/web/20190424180810/http://tanbakuchi.com/posts/comparison-of-openv-interpolation-algorithms/
            return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        # no resize needed, as it is already smaller than the target size
        return image
