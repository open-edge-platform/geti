# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
import os
from collections import defaultdict
from unittest.mock import ANY, MagicMock, patch

import numpy as np
import pytest
from model_api.models.utils import PredictedMask, ZSLVisualPromptingResult
from model_api.models.visual_prompting import SAMLearnableVisualPrompter

from entities.reference_feature import ReferenceFeature, ReferenceMediaInfo
from repos.reference_feature_repo import ReferenceFeatureRepo
from repos.vps_dataset_filter_repo import VPSDatasetFilterRepo, VPSSamplingResult
from services.converters import AnnotationConverter, PromptConverter, VisualPromptingFeaturesConverter
from services.readme import PROMPT_MODEL_README
from services.visual_prompt_service import (
    SAM_DECODER_BIN_PATH_ENV,
    SAM_DECODER_XML_PATH_ENV,
    SAM_ENCODER_BIN_PATH_ENV,
    SAM_ENCODER_XML_PATH_ENV,
    VisualPromptService,
    VPSPredictionResults,
)

from geti_types import DatasetStorageIdentifier, NullMediaIdentifier
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.algorithms.visual_prompting import VISUAL_PROMPTING_MODEL_TEMPLATE_ID
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.entities.annotation import Annotation
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset, NullDataset
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelSchema
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.metrics import MultiScorePerformance, ScoreMetric
from sc_sdk.entities.model import (
    Model,
    ModelConfiguration,
    ModelFormat,
    NullModel,
    TrainingFramework,
    TrainingFrameworkType,
)
from sc_sdk.entities.model_storage import ModelStorage, NullModelStorage
from sc_sdk.entities.model_template import TaskFamily, TaskType
from sc_sdk.entities.project import Project
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.entities.task_node import TaskNode, TaskProperties
from sc_sdk.repos import (
    AnnotationSceneRepo,
    DatasetRepo,
    EvaluationResultRepo,
    LabelSchemaRepo,
    ModelRepo,
    ModelStorageRepo,
    ProjectRepo,
)
from sc_sdk.repos.storage.s3_connector import S3Connector


def return_none(*args, **kwargs) -> None:
    return None


@pytest.fixture(scope="module", autouse=True)
def fxt_s3_env_variables(request):
    """
    Set environment variables required for on-prem storage repo to be instantiated
    """
    os.environ["S3_CREDENTIALS_PROVIDER"] = "local"
    os.environ["S3_SECRET_KEY"] = "secret_key"
    os.environ["S3_ACCESS_KEY"] = "access_key"
    os.environ["S3_HOST"] = "s3_host"
    os.environ["S3_PRESIGNED_URL_ACCESS_KEY"] = "presigned_access_key"
    os.environ["S3_PRESIGNED_URL_SECRET_KEY"] = "presigned_secret_key"

    def remove_env_variable(variable_name: str):
        if variable_name in os.environ:
            del os.environ[variable_name]

    request.addfinalizer(lambda: remove_env_variable("S3_CREDENTIALS_PROVIDER"))
    request.addfinalizer(lambda: remove_env_variable("S3_SECRET_KEY"))
    request.addfinalizer(lambda: remove_env_variable("S3_ACCESS_KEY"))
    request.addfinalizer(lambda: remove_env_variable("S3_HOST"))


@pytest.fixture
def fxt_image(fxt_ote_id) -> Image:
    return Image(
        name="dummy_image.jpg",
        uploader_id="dummy_name",
        id=fxt_ote_id(1),
        width=100,
        height=100,
        size=100,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )


@pytest.fixture(scope="module", autouse=True)
def fxt_vps_envs(fxt_s3_env_variables):
    os.environ[SAM_ENCODER_XML_PATH_ENV] = "dummy_sam_encoder_xml_path"
    os.environ[SAM_ENCODER_BIN_PATH_ENV] = "dummy_sam_encoder_bin_path"
    os.environ[SAM_DECODER_XML_PATH_ENV] = "dummy_sam_decoder_xml_path"
    os.environ[SAM_DECODER_BIN_PATH_ENV] = "dummy_sam_decoder_bin_path"
    yield


@pytest.fixture(scope="module", autouse=True)
def fxt_visual_prompt_service(fxt_vps_envs):
    mock_sam_encoder = MagicMock()
    mock_sam_decoder = MagicMock()
    mock_s3_clients = (MagicMock(), None)
    with (
        patch.object(VisualPromptService, "_load_sam_encoder", return_value=mock_sam_encoder),
        patch.object(VisualPromptService, "_load_sam_mask_decoder", return_value=mock_sam_decoder),
        patch.object(SAMLearnableVisualPrompter, "__init__", new=return_none),
        patch.object(S3Connector, "get_clients", return_value=mock_s3_clients),
    ):
        yield VisualPromptService()


@pytest.fixture
def fxt_task_node(fxt_project, fxt_ote_id):
    return TaskNode(
        title="Test node",
        project_id=fxt_project.id_,
        id_=fxt_ote_id(1),
        task_properties=TaskProperties(
            task_type=TaskType.SEGMENTATION,
            task_family=TaskFamily.VISION,
            is_trainable=True,
            is_global=False,
            is_anomaly=False,
        ),
    )


class TestVisualPromptService:
    @pytest.mark.parametrize(
        "label_domain", [Domain.ROTATED_DETECTION, Domain.DETECTION, Domain.SEGMENTATION, Domain.INSTANCE_SEGMENTATION]
    )
    def test_infer(
        self,
        label_domain,
        fxt_project_identifier,
        fxt_visual_prompt_service,
        fxt_image,
        fxt_ote_id,
        fxt_rectangle_annotation,
        fxt_model,
    ) -> None:
        # Arrange
        project_compatible_labels = [
            Label(name="label_1", domain=label_domain, id_=fxt_ote_id(1)),
            Label(name="label_2", domain=label_domain, id_=fxt_ote_id(2)),
            Label(name="label_3", domain=label_domain, id_=fxt_ote_id(3)),
        ]
        task_id = fxt_ote_id(1001)
        learned_label_ids = [fxt_ote_id(1), fxt_ote_id(2)]
        mock_label_schema = MagicMock()
        mock_label_schema.get_all_labels.return_value = project_compatible_labels
        mock_reference_features = MagicMock()
        mock_vp_features = MagicMock()
        dummy_predicted_mask = PredictedMask(mask=np.zeros((100, 100), dtype=np.uint8), scores=[0.5], points=[])
        dummy_vp_results = ZSLVisualPromptingResult(data={0: dummy_predicted_mask})
        mock_predicted_annotations = [fxt_rectangle_annotation]
        expected_results = VPSPredictionResults(
            bboxes=mock_predicted_annotations if label_domain is Domain.DETECTION else [],
            rotated_bboxes=mock_predicted_annotations if label_domain is Domain.ROTATED_DETECTION else [],
            polygons=mock_predicted_annotations
            if label_domain in (Domain.SEGMENTATION, Domain.INSTANCE_SEGMENTATION)
            else [],
        )
        label_source = LabelSource(model_id=fxt_model.id_, model_storage_id=fxt_model.model_storage.id_)
        resized_image_numpy = np.ones((2, 2))

        # Act
        with (
            patch.object(
                ReferenceFeatureRepo, "get_all_ids_by_task_id", return_value=learned_label_ids
            ) as mock_get_learned_ids,
            patch.object(
                ReferenceFeatureRepo, "get_all_by_task_id", return_value=mock_reference_features
            ) as mock_get_all_ref_features,
            patch.object(
                LabelSchemaRepo, "get_latest_view_by_task", return_value=mock_label_schema
            ) as mock_label_schema,
            patch.object(VisualPromptService, "one_shot_learn", return_value=None) as mock_learn,
            patch.object(
                VisualPromptingFeaturesConverter, "convert_to_visual_prompting_features", return_value=mock_vp_features
            ) as mock_convert_vp_features,
            patch.object(SAMLearnableVisualPrompter, "infer", return_value=dummy_vp_results) as mock_vp_infer,
            patch.object(
                AnnotationConverter, "convert_to_bboxes", return_value=mock_predicted_annotations
            ) as mock_convert_to_bbox,
            patch.object(
                AnnotationConverter, "convert_to_rotated_bboxes", return_value=mock_predicted_annotations
            ) as mock_convert_to_rot_bbox,
            patch.object(
                AnnotationConverter, "convert_to_polygons", return_value=mock_predicted_annotations
            ) as mock_convert_to_polygons,
            patch.object(
                VisualPromptService, "_get_or_create_sam_model_storage", return_value=fxt_model.model_storage
            ) as mock_get_sam_model_storage,
            patch.object(ModelRepo, "get_one", return_value=fxt_model),
            patch.object(VisualPromptService, "_resize_image", return_value=resized_image_numpy),
        ):
            predicted_annotations = fxt_visual_prompt_service.infer(
                project_identifier=fxt_project_identifier, task_id=task_id, media=fxt_image
            )

        # Assert
        match label_domain:
            case Domain.DETECTION:
                mock_convert_to_bbox.assert_called_once_with(
                    predicted_mask=dummy_predicted_mask,
                    predicted_label=project_compatible_labels[0],
                    label_source=label_source,
                )
            case Domain.ROTATED_DETECTION:
                mock_convert_to_rot_bbox.assert_called_once_with(
                    predicted_mask=dummy_predicted_mask,
                    predicted_label=project_compatible_labels[0],
                    label_source=label_source,
                )
            case Domain.SEGMENTATION | Domain.INSTANCE_SEGMENTATION:
                mock_convert_to_polygons.assert_called_once_with(
                    predicted_mask=dummy_predicted_mask,
                    predicted_label=project_compatible_labels[0],
                    label_source=label_source,
                )
        mock_get_learned_ids.assert_called_once_with(task_id=task_id)
        mock_get_all_ref_features.assert_called_once_with(task_id=task_id)
        mock_label_schema.assert_called_once_with(task_node_id=task_id)
        mock_learn.assert_called_once_with(
            project_identifier=fxt_project_identifier, label_ids=[fxt_ote_id(3)], task_id=task_id
        )
        mock_vp_infer.assert_called_once_with(
            image=resized_image_numpy, reference_features=mock_vp_features, apply_masks_refinement=False
        )
        mock_convert_vp_features.assert_called_once_with(reference_features=mock_reference_features)
        mock_get_sam_model_storage.assert_called_once_with(project_identifier=fxt_project_identifier, task_id=task_id)

        assert predicted_annotations == expected_results

    def test_infer_empty(
        self,
        fxt_project_identifier,
        fxt_visual_prompt_service,
        fxt_image,
        fxt_ote_id,
    ) -> None:
        # Arrange
        task_id = fxt_ote_id(1001)
        mock_label_schema = MagicMock()
        mock_label_schema.get_all_labels.return_value = []
        mock_empty_label = MagicMock()
        mock_label_schema.get_empty_labels.return_value = [mock_empty_label]
        empty_annotation = Annotation(
            shape=Rectangle.generate_full_box(),
            labels=[ScoredLabel(label_id=mock_empty_label.id_, is_empty=True, probability=1.0)],
        )

        # Act
        with (
            patch.object(ReferenceFeatureRepo, "get_all_ids_by_task_id", return_value=[]) as mock_get_learned_ids,
            patch.object(ReferenceFeatureRepo, "get_all_by_task_id", return_value=[]) as mock_get_all_ref_features,
            patch.object(
                LabelSchemaRepo, "get_latest_view_by_task", return_value=mock_label_schema
            ) as mock_label_schema,
        ):
            predicted_annotations = fxt_visual_prompt_service.infer(
                project_identifier=fxt_project_identifier, task_id=task_id, media=fxt_image
            )

        # Assert
        mock_get_learned_ids.assert_called_once_with(task_id=task_id)
        mock_get_all_ref_features.assert_called_once_with(task_id=task_id)
        mock_label_schema.assert_called_once_with(task_node_id=task_id)
        assert len(predicted_annotations.bboxes) == 1
        shape = predicted_annotations.bboxes[0].shape
        assert isinstance(shape, Rectangle)
        assert Rectangle.is_full_box(shape)
        assert predicted_annotations.bboxes[0].get_labels() == empty_annotation.get_labels()
        assert predicted_annotations.rotated_bboxes == []
        assert predicted_annotations.polygons == []

    def test_one_shot_learn(
        self, fxt_project, fxt_visual_prompt_service, fxt_annotation_scene, fxt_image, fxt_ote_id
    ) -> None:
        # Arrange
        task_id = fxt_ote_id(1001)
        label_ids = [fxt_ote_id(1), fxt_ote_id(2)]
        dummy_sampling_result = VPSSamplingResult(
            dataset_storage_identifier=DatasetStorageIdentifier(
                workspace_id=fxt_project.identifier.workspace_id,
                project_id=fxt_project.identifier.project_id,
                dataset_storage_id=fxt_ote_id(10),
            ),
            annotation_scene_id=fxt_annotation_scene.id_,
            label_ids=[fxt_ote_id(1), fxt_ote_id(2)],
        )
        mock_box_prompts = MagicMock()
        mock_polygon_prompts = MagicMock()
        mock_mask = np.zeros((10, 10))
        mock_vp_features_and_masks = (MagicMock(), mock_mask)  # (features, masks)
        mock_ref_features = [MagicMock()]
        mock_sam_infer_results = MagicMock()
        dummy_image_numpy = np.ones((3, 3))
        resized_image_numpy = np.ones((2, 2))
        dummy_image_media = Image(
            uploader_id="test",
            name="dummy_image",
            id=fxt_ote_id(1),
            width=100,
            height=100,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        dataset_item = DatasetItem(id_=fxt_ote_id(100), media=dummy_image_media, annotation_scene=fxt_annotation_scene)

        # Act
        with (
            patch.object(
                VPSDatasetFilterRepo,
                "sample_annotations_by_label_ids",
                return_value=[dummy_sampling_result],
            ) as mock_sample_annotations,
            patch.object(AnnotationSceneRepo, "get_by_id", return_value=fxt_annotation_scene),
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(
                PromptConverter, "extract_bbox_prompts", return_value=mock_box_prompts
            ) as mock_extract_box_prompt,
            patch.object(
                PromptConverter, "extract_polygon_prompts", return_value=mock_polygon_prompts
            ) as mock_extract_polygon_prompt,
            patch.object(SAMLearnableVisualPrompter, "learn", return_value=mock_vp_features_and_masks) as mock_vp_learn,
            patch.object(
                VisualPromptService,
                "_get_2d_media_by_media_identifier",
                return_value=[dummy_image_media, dummy_image_numpy],
            ) as mock_get_numpy,
            patch.object(
                VisualPromptingFeaturesConverter,
                "convert_to_reference_features",
                return_value=mock_ref_features,
            ) as mock_convert_to_ref_features,
            patch.object(VisualPromptingFeaturesConverter, "index_to_label_id", side_effect=label_ids),
            patch.object(ReferenceFeatureRepo, "save_many") as mock_save_ref_features,
            patch.object(VisualPromptService, "_save_sam_model") as mock_save_sam_model,
            patch.object(
                VisualPromptService,
                "_generate_intersection_and_cardinalities",
                return_value=[(0, 100, 200), (1, 50, 100)],
            ) as mock_generate_dice_metrics,
            patch.object(SAMLearnableVisualPrompter, "infer", return_value=mock_sam_infer_results) as mock_sam_infer,
            patch.object(DatasetRepo, "generate_id", return_value=dataset_item.id_),
            patch.object(VisualPromptService, "_resize_image", return_value=resized_image_numpy),
        ):
            reference_features = fxt_visual_prompt_service.one_shot_learn(
                project_identifier=fxt_project.identifier, label_ids=label_ids, task_id=task_id
            )

        # Assert
        mock_sample_annotations.assert_called_once_with(
            label_ids=label_ids, dataset_storage_id=fxt_project.training_dataset_storage_id
        )
        mock_extract_box_prompt.assert_called_once_with(annotation_scene=fxt_annotation_scene, height=2, width=2)
        mock_extract_polygon_prompt.assert_called_once_with(annotation_scene=fxt_annotation_scene, height=2, width=2)
        mock_get_numpy.assert_called_once_with(
            dataset_storage_identifier=dummy_sampling_result.dataset_storage_identifier,
            media_identifier=fxt_annotation_scene.media_identifier,
        )
        mock_vp_learn.assert_called_once_with(
            image=resized_image_numpy, boxes=mock_box_prompts, polygons=mock_polygon_prompts, reset_features=True
        )
        mock_sam_infer.assert_called_once_with(
            image=resized_image_numpy, reference_features=mock_vp_features_and_masks[0], apply_masks_refinement=False
        )
        mock_generate_dice_metrics.assert_called_once_with(
            image_height=2,
            image_width=2,
            reference_masks=mock_mask,
            visual_prompting_result=mock_sam_infer_results,
        )
        mock_convert_to_ref_features.assert_called_once_with(
            visual_prompting_features=mock_vp_features_and_masks[0],
            reference_media_info=ReferenceMediaInfo(
                dataset_storage_id=dummy_sampling_result.dataset_storage_identifier.dataset_storage_id,
                annotation_scene_id=dummy_sampling_result.annotation_scene_id,
                media_identifier=fxt_annotation_scene.media_identifier,
            ),
            task_id=task_id,
        )
        mock_save_ref_features.assert_called_once_with(reference_features)
        mock_save_sam_model.assert_called_once_with(
            project_identifier=fxt_project.identifier,
            task_id=task_id,
            reference_features=reference_features,
            learning_duration=ANY,
            dataset_items=ANY,
            dice_intersection_per_label=defaultdict(int, {label_ids[0]: 100, label_ids[1]: 50}),
            dice_cardinality_per_label=defaultdict(int, {label_ids[0]: 200, label_ids[1]: 100}),
        )
        assert reference_features == mock_ref_features

    def test_save_sam_model(
        self,
        fxt_project,
        fxt_label_schema,
        fxt_task_node,
        fxt_visual_prompt_service,
        fxt_dataset_storage,
        fxt_image,
        fxt_annotation_scene,
        fxt_ote_id,
    ) -> None:
        # Arrange
        label = fxt_label_schema.get_labels(include_empty=False)[0]
        reference_feature = ReferenceFeature(
            label_id=label.id_,
            media_info=ReferenceMediaInfo(
                dataset_storage_id=fxt_ote_id(10),
                annotation_scene_id=fxt_ote_id(11),
                media_identifier=NullMediaIdentifier(),
            ),
            numpy=np.ones((1, 1)),
            task_id=fxt_task_node.id_,
        )
        learning_duration = 42
        model_template = ModelTemplateList().get_by_id(VISUAL_PROMPTING_MODEL_TEMPLATE_ID)
        sam_model_storage = ModelStorage(
            id_=fxt_ote_id(2),
            project_id=fxt_project.id_,
            task_node_id=fxt_task_node.id_,
            model_template=model_template,
        )
        ref_feat_numpy_filename = f"reference_feature{reference_feature.label_id}.npz"
        reference_features_json = json.dumps(
            [
                {
                    "label_id": reference_feature.label_id,
                    "name": label.name,
                    "color": label.color.hex_str,
                    "numpy_filename": ref_feat_numpy_filename,
                }
            ],
            indent=4,
        ).encode()
        model_data_sources = {
            "encoder.xml": b"sam_encoder_xml",
            "encoder.bin": b"sam_encoder_bin",
            "decoder.xml": b"sam_decoder_xml",
            "decoder.bin": b"sam_decoder_bin",
            ref_feat_numpy_filename: b"reference_feature_numpy",
            "reference_features.json": reference_features_json,
            "README.md": PROMPT_MODEL_README.encode(),
        }

        sam_model = Model(
            project=fxt_project,
            model_storage=sam_model_storage,
            train_dataset=NullDataset(),
            configuration=ModelConfiguration(
                configurable_parameters=ConfigurableParameters(header="Default parameters", visible_in_ui=False),
                label_schema=fxt_label_schema,
            ),
            id_=fxt_ote_id(3),
            data_source_dict=model_data_sources,
            training_framework=TrainingFramework(
                type=TrainingFrameworkType.THIRD_PARTY,
                version="1.0",
            ),
            model_format=ModelFormat.OPENVINO,
            training_duration=learning_duration,
        )
        dataset_item = DatasetItem(id_=fxt_ote_id(100), media=fxt_image, annotation_scene=fxt_annotation_scene)
        dice_intersection_per_label = defaultdict(int, {label.id_: 50})
        dice_cardinality_per_label = (defaultdict(int, {label.id_: 100}),)
        reference_dataset = Dataset(items=[dataset_item], id=fxt_ote_id(1000), label_schema_id=fxt_label_schema.id_)

        # Act
        with (
            patch.object(VisualPromptService, "_sam_encoder_xml", return_value=model_data_sources["encoder.xml"]),
            patch.object(VisualPromptService, "_sam_encoder_bin", return_value=model_data_sources["encoder.bin"]),
            patch.object(VisualPromptService, "_sam_decoder_xml", return_value=model_data_sources["decoder.xml"]),
            patch.object(VisualPromptService, "_sam_decoder_bin", return_value=model_data_sources["decoder.bin"]),
            patch.object(VisualPromptService, "_save_sam_evaluation_result") as mock_save_sam_evaluation_result,
            patch.object(Project, "get_trainable_task_nodes", return_value=[fxt_task_node]),
            patch.object(Project, "get_training_dataset_storage", return_value=fxt_dataset_storage),
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                LabelSchemaRepo, "get_latest_view_by_task", return_value=fxt_label_schema
            ) as mock_get_label_schema,
            patch.object(
                ModelStorageRepo, "get_one_by_task_node_id", return_value=NullModelStorage()
            ) as mock_get_model_storage,
            patch.object(ModelStorageRepo, "generate_id", return_value=sam_model_storage.id_),
            patch.object(ModelStorageRepo, "save") as mock_save_model_storage,
            patch.object(ModelRepo, "get_one", return_value=NullModel()) as mock_get_model,
            patch.object(ModelRepo, "generate_id", return_value=sam_model.id_),
            patch.object(ModelRepo, "save") as mock_model_save,
            patch.object(DatasetRepo, "save_deep") as mock_save_reference_dataset,
            patch.object(DatasetRepo, "generate_id", return_value=reference_dataset.id_),
        ):
            fxt_visual_prompt_service._save_sam_model(
                project_identifier=fxt_project.identifier,
                task_id=fxt_task_node.id_,
                reference_features=[reference_feature],
                learning_duration=learning_duration,
                dataset_items=[dataset_item],
                dice_intersection_per_label=dice_intersection_per_label,
                dice_cardinality_per_label=dice_cardinality_per_label,
            )

        # Assert
        mock_get_project.assert_called_once_with(fxt_project.id_)
        mock_get_model_storage.assert_called_once_with(
            task_node_id=fxt_task_node.id_,
            extra_filter={"model_template_id": VISUAL_PROMPTING_MODEL_TEMPLATE_ID},
        )
        mock_get_label_schema.assert_called_once()
        mock_save_model_storage.assert_called_once_with(sam_model_storage)
        mock_get_model.assert_called_once()
        mock_model_save.assert_called_once_with(sam_model)
        mock_save_reference_dataset.assert_called_once()
        mock_save_sam_evaluation_result.assert_called_once_with(
            project_identifier=fxt_project.identifier,
            model=sam_model,
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            dataset=ANY,
            dice_intersection_per_label=dice_intersection_per_label,
            dice_cardinality_per_label=dice_cardinality_per_label,
        )

    def test_save_sam_evaluation_result(
        self,
        fxt_project_identifier,
        fxt_dataset_storage_identifier,
        fxt_dataset,
        fxt_model,
        fxt_visual_prompt_service,
        fxt_label,
        fxt_label_2,
    ) -> None:
        # Arrange
        dice_intersection_per_label = {
            fxt_label.id_: 150,
            fxt_label_2.id_: 50,
        }
        dice_cardinality_per_label = {
            fxt_label.id_: 350,
            fxt_label_2.id_: 150,
        }
        mock_evaluation_result = MagicMock()
        mock_evaluation_result.performance = MultiScorePerformance()
        expected_performance = MultiScorePerformance(
            primary_score=ScoreMetric(name="Dice", value=0.8),
            additional_scores=[
                ScoreMetric(label_id=fxt_label.id_, name="dice_intersection", value=150),
                ScoreMetric(label_id=fxt_label.id_, name="dice_cardinality", value=350),
                ScoreMetric(label_id=fxt_label_2.id_, name="dice_intersection", value=50),
                ScoreMetric(label_id=fxt_label_2.id_, name="dice_cardinality", value=150),
            ],
        )

        # Act
        with (
            patch.object(
                EvaluationResultRepo, "get_latest_by_model_ids", return_value=mock_evaluation_result
            ) as mock_get_latest_evaluation_result,
            patch.object(EvaluationResultRepo, "save", return_value=mock_evaluation_result) as mock_save_evaluation,
            patch.object(LabelSchema, "get_labels", return_value=[fxt_label, fxt_label_2]),
        ):
            fxt_visual_prompt_service._save_sam_evaluation_result(
                project_identifier=fxt_project_identifier,
                model=fxt_model,
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                dataset=fxt_dataset,
                dice_intersection_per_label=dice_intersection_per_label,
                dice_cardinality_per_label=dice_cardinality_per_label,
            )

        # Assert
        mock_get_latest_evaluation_result.assert_called_once_with([fxt_model.id_])
        mock_save_evaluation.assert_called_once_with(mock_evaluation_result)
        assert mock_evaluation_result.performance == expected_performance
