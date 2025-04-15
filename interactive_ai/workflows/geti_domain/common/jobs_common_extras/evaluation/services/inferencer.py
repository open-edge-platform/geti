# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Inferencer services"""

import io
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from enum import Enum, auto
from typing import Any, NamedTuple, cast

import numpy as np
from geti_telemetry_tools import unified_tracing
from geti_types import DatasetStorageIdentifier
from media_utils import get_media_roi_numpy
from model_api.adapters.openvino_adapter import OpenvinoAdapter, create_core
from model_api.models import ImageModel, SAMDecoder, SAMImageEncoder, SAMLearnableVisualPrompter, SegmentationModel
from model_api.models.utils import (
    AnomalyResult,
    ClassificationResult,
    DetectionResult,
    ImageResultWithSoftPrediction,
    ZSLVisualPromptingResult,
)
from model_api.models.visual_prompting import VisualPromptingFeatures
from model_api.tilers import DetectionTiler, InstanceSegmentationTiler
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.label import Domain
from sc_sdk.entities.media_2d import Media2D
from sc_sdk.entities.metadata import FloatMetadata, FloatType, IMetadata
from sc_sdk.entities.model import Model
from sc_sdk.entities.model_template import TaskType
from sc_sdk.entities.tensor import Tensor
from sc_sdk.repos import AnnotationSceneRepo

from jobs_common_extras.evaluation.utils.configuration_utils import get_tiler_configuration, get_tiling_parameters
from jobs_common_extras.evaluation.utils.detection_utils import get_legacy_detection_inferencer_configuration
from jobs_common_extras.evaluation.utils.helpers import downscale_image, is_model_legacy_otx_version
from jobs_common_extras.evaluation.utils.metadata_utils import Metadata
from jobs_common_extras.evaluation.utils.segmentation_utils import (
    get_legacy_instance_segmentation_inferencer_configuration,
)

from .prediction_to_annotation_converter import (
    AnomalyToAnnotationConverter,
    ClassificationToAnnotationConverter,
    DetectionToAnnotationConverter,
    InstanceSegmentationToAnnotationConverter,
    KeypointToAnnotationConverter,
    RotatedRectToAnnotationConverter,
    SemanticSegmentationToAnnotationConverter,
    VisualPromptingToAnnotationConverter,
)

logger = logging.getLogger(__name__)


class WeightsKey(Enum):
    OPENVINO_XML = "openvino.xml"
    OPENVINO_BIN = "openvino.bin"
    TILE_CLASSIFIER_XML = "tile_classifier.xml"
    TILE_CLASSIFIER_BIN = "tile_classifier.bin"
    VISUAL_PROMPTING_ENCODER_XML = "encoder.xml"
    VISUAL_PROMPTING_ENCODER_BIN = "encoder.bin"
    VISUAL_PROMPTING_DECODER_XML = "decoder.xml"
    VISUAL_PROMPTING_DECODER_BIN = "decoder.bin"
    VISUAL_PROMPTING_REFERENCE_FEATURES_JSON = "reference_features.json"


class PerformanceHint(Enum):
    """
    Enum representing the performance hint to be used for the OpenVINO adapter.

    LATENCY         Prioritizes low latency. Best suited for real-time applications.
    THROUGHPUT      Prioritizes high throughput. Best suited for inference on large numbers of images.
    """

    LATENCY = auto()
    THROUGHPUT = auto()


class Inferencer(ABC):
    """
    Abstract base class representing a wrapper over ModelAPI for handling the inference pipeline.

    Concrete classes implementing this interface are responsible for initializing ModelAPI adapters with
    the necessary configurations and converting the prediction results to an AnnotationScene.

    :param model: The model to be used for running inference.
    :param device: Device to run inference on, such as CPU, GPU or MYRIAD. Defaults to "CPU".
    :param max_async_requests: Maximum number of concurrent requests that the asynchronous inferencer can make.
        Defaults to 0 (OpenVINO will try to select an optimal value based on the number of available CPU cores).
    :param performance_hint: Performance hint to be used for the OpenVINO adapter. Defaults to "THROUGHPUT".
    """

    def __init__(
        self,
        model: Model,
        device: str = "CPU",
        max_async_requests: int = 0,
        performance_hint: PerformanceHint = PerformanceHint.THROUGHPUT,
    ):
        self.is_legacy_otx_model = is_model_legacy_otx_version(model)
        self.label_schema = model.get_label_schema()
        self.geti_model = model
        self._openvino_core = create_core()
        logger.info(
            f"Creating OpenVINO adapter with max_async_requests: {max_async_requests} "
            f"(only valid for asynchronous inferencer)"
        )
        if {WeightsKey.OPENVINO_BIN.value, WeightsKey.OPENVINO_XML.value} - model.model_adapters.keys():
            raise ValueError(f"Model with ID '{model.id_}' does not contain the required OpenVINO model weights.")
        self.model_adapter = OpenvinoAdapter(
            self._openvino_core,
            model=model.model_adapters[WeightsKey.OPENVINO_XML.value].data,
            weights_path=model.model_adapters[WeightsKey.OPENVINO_BIN.value].data,
            device=device,
            max_num_requests=max_async_requests,
            plugin_config={"PERFORMANCE_HINT": performance_hint.name},
        )
        self.configuration = self.get_configuration()
        self.model = ImageModel.create_model(model=self.model_adapter, configuration=self.configuration, preload=True)
        self.model.inference_adapter.set_callback(self._async_callback)
        self.tiling_enabled = False

    @abstractmethod
    def convert_to_annotations(self, raw_predictions: NamedTuple, **kwargs) -> list[Annotation]:
        """Converts a raw prediction to an AnnotationScene"""

    @abstractmethod
    def get_configuration(self) -> dict:
        """Additional model configuration"""
        return {}

    def _extract_metadata(
        self,
        raw_predictions: ClassificationResult | DetectionResult | ImageResultWithSoftPrediction,
        annotation_scene: AnnotationScene,  # noqa: ARG002
    ) -> list[IMetadata]:
        """
        Extracts metadata from raw predictions, including:
            - active score (classification)
            - feature vector
        """
        feature_vector = raw_predictions.feature_vector
        metadata: list[IMetadata] = []
        if len(feature_vector) > 0:
            metadata.append(Tensor(name=Metadata.REPRESENTATION_VECTOR.value, numpy=feature_vector.reshape(-1)))
        return metadata

    @unified_tracing
    def _predict_raw(self, image: np.ndarray) -> tuple[NamedTuple, dict]:
        """
        Predicts on the input image using ModelAPI and returns its raw results and metadata.

        :param image: the image to get predictions for
        :return: a tuple containing:
            - NamedTuple containing the raw prediction results
            - dictionary containing metadata
        """
        processed_image, metadata = self.model.preprocess(image)
        raw_result = self.model.infer_sync(processed_image)
        result = self.model.postprocess(raw_result, metadata)
        return result, metadata

    @unified_tracing
    def predict(
        self,
        dataset_storage_id: DatasetStorageIdentifier,
        media: Media2D,
        roi: Annotation | None = None,
        annotation_scene: AnnotationScene | None = None,
    ) -> tuple[AnnotationScene, Sequence[IMetadata]]:
        """
        Performs inference on the given image and returns the prediction results.

        :param dataset_storage_id: Dataset storage identifier
        :param media: The media (image or video frame) for which predictions are to be made.
            The media is expected to be an RGB array of shape (Height, Width, Channels) with uint8 type (0-255).
        :param roi: The region of interest (ROI) to be used for inference. Defaults to None.
        :param annotation_scene: optional annotation scene object to add annotations to
        :return: A tuple containing:
            - AnnotationScene object containing prediction results
            - sequence of metadata generated by the inference
        """
        numpy_image = get_media_roi_numpy(
            dataset_storage_identifier=dataset_storage_id,
            media=media,
            roi_shape=roi.shape if roi is not None else None,
        )
        result, metadata = self._predict_raw(numpy_image)
        annotations = self.convert_to_annotations(raw_predictions=result, metadata=metadata)
        if annotation_scene is None:
            annotation_scene = AnnotationScene(
                kind=AnnotationSceneKind.PREDICTION,
                media_identifier=media.media_identifier,
                media_height=media.height,
                media_width=media.width,
                id_=AnnotationSceneRepo.generate_id(),
            )
        annotation_scene.append_annotations(annotations)
        result_metadata = self._extract_metadata(raw_predictions=result, annotation_scene=annotation_scene)
        return annotation_scene, result_metadata

    def _async_callback(self, request: Any, callback_args: tuple) -> None:
        """
        Fetches the results of async inference.

        :param request: the ModelAPI request object
        :param callback_args: the arguments to the callback function
        """
        try:
            item_idx, media, preprocessing_meta, result_handler = callback_args
            raw_prediction = self.model.inference_adapter.get_raw_result(request)
            processed_prediction = self.model.postprocess(raw_prediction, preprocessing_meta)
            annotations = self.convert_to_annotations(raw_predictions=processed_prediction, metadata=preprocessing_meta)
            annotation_scene = AnnotationScene(
                kind=AnnotationSceneKind.PREDICTION,
                media_identifier=media.media_identifier,
                media_height=media.height,
                media_width=media.width,
                id_=AnnotationSceneRepo.generate_id(),
                annotations=annotations,
            )
            result_metadata = self._extract_metadata(
                raw_predictions=processed_prediction, annotation_scene=annotation_scene
            )
            result_handler(item_idx, annotation_scene, result_metadata)
        except Exception as e:
            logger.exception(f"Error while processing async callback: {e}")
            raise e

    def enqueue_prediction(
        self,
        dataset_storage_id: DatasetStorageIdentifier,
        item_idx: int,
        media: Media2D,
        result_handler: Callable[[int, AnnotationScene, Sequence[IMetadata]], None],
        roi: Annotation | None = None,
    ) -> None:
        """
        Enqueues the prediction request for the given media.

        Note: If tiling classifier is enabled, the prediction is made using the sync API.

        :param dataset_storage_id: Dataset storage identifier
        :param item_idx: the index of the item for which the prediction is being made
        :param media: the media (image or video frame) for which predictions are to be made
        :param result_handler: the callback function to handle the prediction results
        :param roi: the region of interest (ROI) to be used for inference. Defaults to None.
        """
        # If tiling is enabled, predict using the synchronous method
        # The tiling model runs prediction using the async API for each image tile
        if self.tiling_enabled:
            pred_ann_scene, metadata = self.predict(dataset_storage_id=dataset_storage_id, media=media, roi=roi)
            result_handler(item_idx, pred_ann_scene, metadata)
            return
        numpy_image = get_media_roi_numpy(
            dataset_storage_identifier=dataset_storage_id,
            media=media,
            roi_shape=roi.shape if roi is not None else None,
        )
        img, metadata = self.model.preprocess(numpy_image)
        callback_data = item_idx, media, metadata, result_handler
        self.model.infer_async_raw(img, callback_data)

    def await_all(self) -> None:
        """Await all running infer requests if any."""
        self.model.await_all()


class ClassificationInferencer(Inferencer):
    def __init__(self, model: Model, **kwargs):
        super().__init__(model=model, **kwargs)
        self._converter = ClassificationToAnnotationConverter(
            label_schema=self.label_schema, model_api_labels=self.model.labels
        )

    def get_configuration(self) -> dict:
        configuration = super().get_configuration()
        if "labels" in configuration:
            configuration.pop("labels")
        # create a dummy hierarchical config for backward compatibility, which is not actually used
        if configuration.get("hierarchical"):
            try:
                self.model_adapter.get_rt_info(["model_info", "hierarchical_config"])
            except RuntimeError:
                configuration["hierarchical_config"] = json.dumps(
                    {"cls_heads_info": {"label_to_idx": [], "all_groups": []}, "label_tree_edges": []}
                )
        return configuration

    def convert_to_annotations(self, raw_predictions: NamedTuple, **kwargs) -> list[Annotation]:
        return self._converter.convert_to_annotations(predictions=raw_predictions, **kwargs)

    def _extract_metadata(
        self, raw_predictions: ClassificationResult, annotation_scene: AnnotationScene
    ) -> list[IMetadata]:
        super_metadata = super()._extract_metadata(raw_predictions=raw_predictions, annotation_scene=annotation_scene)
        probs = raw_predictions.raw_scores
        active_score = np.max(probs) - np.min(probs)
        active_score_metadata = FloatMetadata(
            name=Metadata.ACTIVE_SCORE.value, value=active_score, float_type=FloatType.ACTIVE_SCORE
        )
        return [*super_metadata, active_score_metadata]


class DetectionInferencer(Inferencer):
    def __init__(self, model: Model, **kwargs):
        super().__init__(model=model, **kwargs)
        self._converter = DetectionToAnnotationConverter(
            label_schema=self.label_schema, model_api_labels=self.model.labels, configuration=self.configuration
        )
        self.tiling_parameters = get_tiling_parameters(model=model)
        self.tiling_enabled = self.tiling_parameters["enable_tiling"]
        if self.tiling_enabled:
            logger.info(f"Tiling is enabled for model with ID {model.id_}.")
            tiler_config = (
                get_tiler_configuration(tiling_parameters=self.tiling_parameters) if self.is_legacy_otx_model else {}
            )
            self.tiler = DetectionTiler(model=self.model, configuration=tiler_config)

    def convert_to_annotations(self, raw_predictions: NamedTuple, **kwargs) -> list[Annotation]:
        return self._converter.convert_to_annotations(predictions=raw_predictions, **kwargs)

    def get_configuration(self) -> dict:
        configuration = super().get_configuration()
        if self.is_legacy_otx_model:
            otx_legacy_config = get_legacy_detection_inferencer_configuration(model=self.geti_model)
            configuration.update(otx_legacy_config)
        logger.info(f"Detection inferencer configuration: {configuration}")
        return configuration

    def _predict_raw(self, image: np.ndarray) -> tuple[NamedTuple, dict]:
        """
        Predicts on the input image using ModelAPI and returns its raw results and metadata.

        If tiling is enabled, the image is divided into smaller tiles, and predictions are made for each tile.
        The tiles are then combined to form the final prediction.

        :param image: the image to get predictions for
        :return: a tuple containing:
            - NamedTuple containing the raw prediction results
            - dictionary containing metadata
        """
        if not self.tiling_enabled:
            return super()._predict_raw(image)
        # Use tiler if enabled
        metadata = {"original_shape": image.shape}
        return self.tiler(image), metadata


class RotatedDetectionInferencer(DetectionInferencer):
    def __init__(self, model: Model, device: str = "CPU", max_async_requests: int = 0):
        super().__init__(model=model, device=device, max_async_requests=max_async_requests)
        self._converter = RotatedRectToAnnotationConverter(
            label_schema=self.label_schema, model_api_labels=self.model.labels, configuration=self.configuration
        )
        self.tiling_classifier_enabled = self.tiling_parameters["enable_tile_classifier"]
        tile_classifier_model = None
        if self.tiling_enabled and self.tiling_classifier_enabled and self.is_legacy_otx_model:
            # tile_classifier_model is an additional model that requires a separate adapter
            # it is used to speedup of tiling inference by skipping tiles where no objects are detected
            # it is only supported for legacy OTX models
            if {
                WeightsKey.TILE_CLASSIFIER_BIN.value,
                WeightsKey.TILE_CLASSIFIER_XML.value,
            } - model.model_adapters.keys():
                raise ValueError(
                    f"Model with ID '{model.id_}' is configured with a tile classifier model "
                    f"but does not contain the required weights."
                )
            tile_class_adapter = OpenvinoAdapter(
                self._openvino_core,
                model=model.model_adapters[WeightsKey.TILE_CLASSIFIER_XML.value].data,
                weights_path=model.model_adapters[WeightsKey.TILE_CLASSIFIER_BIN.value].data,
                device=device,
                max_num_requests=max_async_requests,
            )
            tile_classifier_model = ImageModel(inference_adapter=tile_class_adapter, configuration={}, preload=True)
        if self.tiling_enabled:
            tiler_config = (
                get_tiler_configuration(tiling_parameters=self.tiling_parameters) if self.is_legacy_otx_model else {}
            )
            self.tiler = InstanceSegmentationTiler(
                model=self.model, configuration=tiler_config, tile_classifier_model=tile_classifier_model
            )


class SemanticSegmentationInferencer(Inferencer):
    def __init__(self, model: Model, **kwargs):
        super().__init__(model=model, **kwargs)
        self._converter = SemanticSegmentationToAnnotationConverter(
            label_schema=self.label_schema, model=cast("SegmentationModel", self.model)
        )

    def convert_to_annotations(self, raw_predictions: NamedTuple, **kwargs) -> list[Annotation]:
        return self._converter.convert_to_annotations(predictions=raw_predictions, **kwargs)

    def get_configuration(self) -> dict:
        # Semantic segmentation model does not require extra config parameters
        return super().get_configuration()


class InstanceSegmentationInferencer(Inferencer):
    def __init__(self, model: Model, device: str = "CPU", max_async_requests: int = 0):
        super().__init__(model=model, device=device, max_async_requests=max_async_requests)
        self._converter = InstanceSegmentationToAnnotationConverter(
            label_schema=self.label_schema, model_api_labels=self.model.labels, configuration=self.configuration
        )
        self.tiling_parameters = get_tiling_parameters(model=model)
        self.tiling_enabled = self.tiling_parameters["enable_tiling"]
        self.tiling_classifier_enabled = self.tiling_parameters["enable_tile_classifier"]
        tile_classifier_model = None
        if self.tiling_enabled and self.tiling_classifier_enabled and self.is_legacy_otx_model:
            # tile_classifier_model is an additional model that requires a separate adapter
            # it is used to speedup of tiling inference by skipping tiles where no objects are detected
            # it is only supported for legacy OTX models
            if {
                WeightsKey.TILE_CLASSIFIER_BIN.value,
                WeightsKey.TILE_CLASSIFIER_XML.value,
            } - model.model_adapters.keys():
                raise ValueError(
                    f"Model with ID '{model.id_}' is configured with a tile classifier model "
                    f"but does not contain the required weights."
                )
            tile_class_adapter = OpenvinoAdapter(
                self._openvino_core,
                model=model.model_adapters[WeightsKey.TILE_CLASSIFIER_XML.value].data,
                weights_path=model.model_adapters[WeightsKey.TILE_CLASSIFIER_BIN.value].data,
                device=device,
                max_num_requests=max_async_requests,
            )
            tile_classifier_model = ImageModel(inference_adapter=tile_class_adapter, configuration={}, preload=True)
        if self.tiling_enabled:
            tiler_config = (
                get_tiler_configuration(tiling_parameters=self.tiling_parameters) if self.is_legacy_otx_model else {}
            )
            self.tiler = InstanceSegmentationTiler(
                model=self.model, configuration=tiler_config, tile_classifier_model=tile_classifier_model
            )

    def convert_to_annotations(self, raw_predictions: NamedTuple, **kwargs) -> list[Annotation]:
        return self._converter.convert_to_annotations(predictions=raw_predictions, **kwargs)

    def get_configuration(self) -> dict:
        configuration = super().get_configuration()
        if self.is_legacy_otx_model:
            otx_legacy_config = get_legacy_instance_segmentation_inferencer_configuration(model=self.geti_model)
            configuration.update(otx_legacy_config)
        return configuration

    def _predict_raw(self, image: np.ndarray) -> tuple[NamedTuple, dict]:
        """
        Predicts on the input image using ModelAPI and returns its raw results and metadata.

        If tiling is enabled, the image is divided into smaller tiles, and predictions are made for each tile.
        The tiles are then combined to form the final prediction.

        :param image: the image to get predictions for
        :return: a tuple containing:
            - NamedTuple containing the raw prediction results
            - dictionary containing metadata
        """
        if not self.tiling_enabled:
            return super()._predict_raw(image)
        # Use tiler if enabled
        metadata = {"original_shape": image.shape}
        return self.tiler(image), metadata


class AnomalyInferencer(Inferencer):
    def __init__(self, model: Model, **kwargs):
        super().__init__(model=model, **kwargs)
        self._converter = AnomalyToAnnotationConverter(label_schema=self.label_schema)

        # Backward compatibility for model trained with OTX<=1.4:
        # set default parameter for "normalization_scale" if not present in the model configuration
        if not self.model.normalization_scale:
            self.model.normalization_scale = 1.0

    def convert_to_annotations(self, raw_predictions: NamedTuple, **kwargs) -> list[Annotation]:
        return self._converter.convert_to_annotations(predictions=raw_predictions, **kwargs)

    def get_configuration(self) -> dict:
        # Anomaly models do not require extra config parameters
        return super().get_configuration()

    def _extract_metadata(
        self,
        raw_predictions: AnomalyResult,  # noqa: ARG002
        annotation_scene: AnnotationScene,  # noqa: ARG002
    ) -> list[IMetadata]:
        # No metadata needs to be returned for anomaly models
        return []


class VisualPromptingInferencer(Inferencer):
    def __init__(
        self,
        model: Model,
        device: str = "CPU",
        max_async_requests: int = 0,
        performance_hint: PerformanceHint = PerformanceHint.THROUGHPUT,
    ):
        self.label_schema = model.get_label_schema()
        self.geti_model = model
        self._openvino_core = create_core()
        self.configuration = self.get_configuration()
        self.tiling_enabled = False
        self._load_sam_model(device=device, max_async_requests=max_async_requests, performance_hint=performance_hint)
        self._converter = VisualPromptingToAnnotationConverter(
            label_schema=self.geti_model.get_label_schema(), model_api_labels=self.learned_label_ids
        )

    def _load_sam_model(self, device: str, max_async_requests: int, performance_hint: PerformanceHint) -> None:
        """Loads the SAM encoder and decoder models along with the reference features required for visual prompting."""
        logger.info(f"Creating SAM encoder and decoder models with max_async_requests: {max_async_requests}")
        missing_model_weights = {
            WeightsKey.VISUAL_PROMPTING_ENCODER_XML.value,
            WeightsKey.VISUAL_PROMPTING_ENCODER_BIN.value,
            WeightsKey.VISUAL_PROMPTING_DECODER_BIN.value,
            WeightsKey.VISUAL_PROMPTING_DECODER_XML.value,
            WeightsKey.VISUAL_PROMPTING_REFERENCE_FEATURES_JSON.value,
        } - self.geti_model.model_adapters.keys()
        if missing_model_weights:
            raise ValueError(
                f"Model with ID '{self.geti_model.id_}' does not contain the required visual prompting "
                f"model weights {missing_model_weights}."
            )

        # load encoder and decoder models
        encoder_adapter = OpenvinoAdapter(
            self._openvino_core,
            model=self.geti_model.get_data(WeightsKey.VISUAL_PROMPTING_ENCODER_XML.value),
            weights_path=self.geti_model.get_data(WeightsKey.VISUAL_PROMPTING_ENCODER_BIN.value),
            device=device,
            max_num_requests=max_async_requests,
            plugin_config={"PERFORMANCE_HINT": performance_hint.name},
        )
        encoder = SAMImageEncoder(
            inference_adapter=encoder_adapter,
            preload=True,
        )
        decoder_adapter = OpenvinoAdapter(
            self._openvino_core,
            model=self.geti_model.get_data(WeightsKey.VISUAL_PROMPTING_DECODER_XML.value),
            weights_path=self.geti_model.get_data(WeightsKey.VISUAL_PROMPTING_DECODER_BIN.value),
            device=device,
            max_num_requests=max_async_requests,
            plugin_config={"PERFORMANCE_HINT": performance_hint.name},
        )
        decoder = SAMDecoder(
            model_adapter=decoder_adapter,
            preload=True,
        )

        # load reference features
        reference_features_dict = json.loads(
            self.geti_model.get_data(WeightsKey.VISUAL_PROMPTING_REFERENCE_FEATURES_JSON.value)
        )
        feature_vectors = []
        used_indices = []
        self.learned_label_ids = []
        for idx, (label_id_str, ref_feat_info) in enumerate(reference_features_dict.items()):
            vector_bytes = io.BytesIO(self.geti_model.get_data(ref_feat_info["numpy_filename"]))
            vector_numpy = np.load(vector_bytes)["array"]
            feature_vectors.append(vector_numpy)
            used_indices.append(idx)
            self.learned_label_ids.append(label_id_str)
        reference_features = VisualPromptingFeatures(feature_vectors=feature_vectors, used_indices=used_indices)

        self.model = SAMLearnableVisualPrompter(
            encoder_model=encoder,
            decoder_model=decoder,
            reference_features=reference_features,
        )

    def convert_to_annotations(self, raw_predictions: NamedTuple, **kwargs) -> list[Annotation]:
        # Label mapping is required because ModelAPI uses an index-based representation for labels
        return self._converter.convert_to_annotations(predictions=raw_predictions, **kwargs)

    def get_configuration(self) -> dict:
        # Visual prompting models do not require extra config parameters
        return {}

    def enqueue_prediction(
        self,
        dataset_storage_id: DatasetStorageIdentifier,
        item_idx: int,
        media: Media2D,
        result_handler: Callable[[int, AnnotationScene, Sequence[IMetadata]], None],
        roi: Annotation | None = None,
    ) -> None:
        raise NotImplementedError("Visual prompting models do not support asynchronous inference.")

    def _extract_metadata(
        self,
        raw_predictions: ZSLVisualPromptingResult,  # noqa: ARG002
        annotation_scene: AnnotationScene,  # noqa: ARG002
    ) -> list[IMetadata]:
        # No metadata needs to be returned for visual prompting models
        return []

    def _predict_raw(self, image: np.ndarray) -> tuple[NamedTuple, dict]:
        """
        Predicts on the input image using ModelAPI and returns its raw results and metadata.

        :param image: the image to get predictions for
        :return: a tuple containing:
            - NamedTuple containing the raw prediction results
            - dictionary containing metadata
        """
        # SAM uses an internal resolution of 1024x1024
        _image = downscale_image(image, target_largest_size=1024)
        metadata = {"original_shape": _image.shape}
        return self.model.infer(image=_image, apply_masks_refinement=False), metadata


class KeypointDetectionInferencer(Inferencer):
    def __init__(self, model: Model, **kwargs):
        super().__init__(model=model, **kwargs)
        self._converter = KeypointToAnnotationConverter(
            label_schema=self.label_schema,
            model_api_labels=self.model.labels,
        )

    def convert_to_annotations(self, raw_predictions: NamedTuple, **kwargs) -> list[Annotation]:
        return self._converter.convert_to_annotations(predictions=raw_predictions, **kwargs)

    def get_configuration(self) -> dict:
        # Keypoint detection models do not require extra config parameters
        return super().get_configuration()

    def _extract_metadata(
        self,
        raw_predictions: ZSLVisualPromptingResult,  # noqa: ARG002
        annotation_scene: AnnotationScene,  # noqa: ARG002
    ) -> list[IMetadata]:
        # There is no metadata to be returned for keypoint detection models
        return []


class InferencerFactory:
    @staticmethod
    def create_inferencer(model: Model, device: str = "CPU", max_async_requests: int = 0) -> Inferencer:
        """
        Creates the appropriate inferencer object according to the model's task.

        :param model: the model to be used for inference
        :param device: Device to run inference on, such as CPU, GPU or MYRIAD. Defaults to "CPU".
        :param max_async_requests: Maximum number of concurrent requests that the asynchronous inferencer can make.
            Defaults to 0 (OpenVINO will try to select an optimal value based on the number of available CPU cores).
        :return: inferencer object
        """
        inferencer: Inferencer

        # use task type as the visual prompting model can be mapped to multiple label domains
        if model.model_storage.model_template.task_type is TaskType.VISUAL_PROMPTING:
            return VisualPromptingInferencer(model, device=device, max_async_requests=max_async_requests)

        # we need to use label domain as the model_template is not available for all models when OTX is not installed
        domain = InferencerFactory._get_labels_domain(model)
        match domain:
            case Domain.CLASSIFICATION:
                inferencer = ClassificationInferencer(model, device=device, max_async_requests=max_async_requests)
            case Domain.DETECTION:
                inferencer = DetectionInferencer(model, device=device, max_async_requests=max_async_requests)
            case Domain.SEGMENTATION:
                inferencer = SemanticSegmentationInferencer(model, device=device, max_async_requests=max_async_requests)
            case Domain.INSTANCE_SEGMENTATION:
                inferencer = InstanceSegmentationInferencer(model, device=device, max_async_requests=max_async_requests)
            case Domain.ROTATED_DETECTION:
                inferencer = RotatedDetectionInferencer(model, device=device, max_async_requests=max_async_requests)
            case Domain.ANOMALY_CLASSIFICATION | Domain.ANOMALY_SEGMENTATION | Domain.ANOMALY_DETECTION:
                inferencer = AnomalyInferencer(model, device=device, max_async_requests=max_async_requests)
            case Domain.KEYPOINT_DETECTION:
                inferencer = KeypointDetectionInferencer(model, device=device, max_async_requests=max_async_requests)
            case _:
                raise ValueError(f"Cannot create inferencer for task type '{domain.name}' and model ID `{model.id_}`")
        return inferencer

    @staticmethod
    def _get_labels_domain(model: Model) -> Domain:
        """Returns the domain (task type) associated with the model's labels"""
        label_schema = model.get_label_schema()
        try:
            return next(label.domain for label in label_schema.get_labels(include_empty=False))
        except StopIteration:
            raise ValueError(f"Cannot determine the task for model with ID '{model.id_}'")
