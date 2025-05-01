# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import io
import logging
from unittest.mock import ANY, call, patch
from uuid import UUID

import numpy as np
import pytest
from bson import ObjectId
from testfixtures import compare

from sc_sdk.adapters.adapter import ProxyAdapter
from sc_sdk.adapters.tensor_adapter import TensorAdapter
from sc_sdk.entities.active_model_state import ActiveModelState
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from sc_sdk.entities.annotation_template import AnnotationTemplate
from sc_sdk.entities.color import Color
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.evaluation_result import EvaluationResult
from sc_sdk.entities.keypoint_structure import KeypointEdge, KeypointPosition, KeypointStructure
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.metadata import FloatMetadata, FloatType, MetadataItem
from sc_sdk.entities.metrics import (
    AnomalyLocalizationPerformance,
    BarChartInfo,
    BarMetricsGroup,
    CurveMetric,
    LineChartInfo,
    LineMetricsGroup,
    MatrixChartInfo,
    MatrixMetric,
    MatrixMetricsGroup,
    MultiScorePerformance,
    Performance,
    ScoreMetric,
    TextChartInfo,
    TextMetricsGroup,
    VisualizationType,
)
from sc_sdk.entities.model import Model, ModelFormat, ModelOptimizationType, ModelPrecision, ModelPurgeInfo, ModelStatus
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.model_template import NullModelTemplate, TaskFamily, TaskType
from sc_sdk.entities.project import Project
from sc_sdk.entities.project_performance import (
    GlobalLocalTaskPerformance,
    ProjectPerformance,
    TaskPerformance,
    TaskPerformanceScore,
)
from sc_sdk.entities.scored_label import LabelSource, ScoredLabel
from sc_sdk.entities.shapes import Ellipse, Keypoint, Point, Polygon, Rectangle
from sc_sdk.entities.subset import Subset
from sc_sdk.entities.suspended_scenes import SuspendedAnnotationScenesDescriptor
from sc_sdk.entities.task_graph import TaskEdge, TaskGraph
from sc_sdk.entities.task_node import TaskNode, TaskProperties
from sc_sdk.entities.tensor import Tensor
from sc_sdk.entities.video_annotation_range import RangeLabels, VideoAnnotationRange
from sc_sdk.repos import (
    AnnotationSceneRepo,
    DatasetRepo,
    DatasetStorageRepo,
    EvaluationResultRepo,
    ImageRepo,
    LabelRepo,
    MetadataRepo,
    ModelRepo,
    ModelStorageRepo,
    ProjectRepo,
    TaskNodeRepo,
    VideoRepo,
)
from sc_sdk.repos.dataset_repo import _DatasetItemRepo
from sc_sdk.repos.mappers import (
    ActiveModelStateToMongo,
    AnnotationSceneStateToMongo,
    AnnotationSceneToMongo,
    DatasetStorageToMongo,
    DatasetToMongo,
    EvaluationResultToMongo,
    FloatMetadataToMongo,
    IDToMongo,
    ImageToMongo,
    LabelGroupToMongo,
    LabelSchemaToMongo,
    LabelToMongo,
    MediaScoreToMongo,
    ModelStorageToMongo,
    ModelTestResultToMongo,
    ModelToMongo,
    NumpyToMongo,
    PerformanceToMongo,
    ProjectToMongo,
    ScoredLabelToMongo,
    SuspendedAnnotationScenesDescriptorToMongo,
    TaskNodeToMongo,
    TensorToMongo,
    VideoAnnotationRangeToMongo,
    VideoIdentifierToMongo,
    VideoToMongo,
)
from sc_sdk.repos.mappers.mongodb_mappers.annotation_template_mapper import AnnotationTemplateToMongo
from sc_sdk.repos.mappers.mongodb_mappers.dataset_mapper import AnnotationSceneCache, DatasetItemToMongo
from sc_sdk.repos.mappers.mongodb_mappers.dataset_storage_filter_mapper import DatasetStorageFilterDataToMongo
from sc_sdk.repos.mappers.mongodb_mappers.metadata_mapper import (
    MetadataItemMapperBackwardParameters,
    MetadataItemToMongo,
    TensorMapperBackwardParameters,
)
from sc_sdk.repos.mappers.mongodb_mappers.model_mapper import TrainingFrameworkToMongo
from sc_sdk.repos.mappers.mongodb_mappers.project_mapper import KeypointStructureToMongo
from sc_sdk.repos.mappers.mongodb_mappers.project_performance_mapper import ProjectPerformanceToMongo
from sc_sdk.repos.mappers.mongodb_mappers.session_mapper import SessionToMongo
from sc_sdk.repos.mappers.mongodb_mappers.training_revision_mapper import TrainingRevisionToMongo
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.project_factory import ProjectFactory
from sc_sdk.utils.time_utils import now
from tests.test_helpers import (
    empty_model_configuration,
    generate_inference_dataset_of_all_media_in_project,
    generate_random_annotated_project,
    generate_training_dataset_of_all_annotated_media_in_project,
    register_model_template,
    verify_mongo_mapper,
)

from geti_types import ID, ImageIdentifier, Session, VideoIdentifier
from geti_types.session import DEFAULT_ORGANIZATION_ID

logger = logging.getLogger(__name__)

FEATURE_FLAG_KEYPOINT_DETECTION = "FEATURE_FLAG_KEYPOINT_DETECTION"


@pytest.fixture
def fxt_video_project(request):
    project = ProjectFactory.create_project_single_task(
        name="__Test video tester",
        description="",
        creator_id="",
        labels=[
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ],
        model_template_id="segmentation",
    )
    request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))
    yield project


class TestStaticMongoDBMappers:
    @pytest.mark.parametrize("enable_keypoint_detection", [True, False])
    def test_project_mapper(self, request, fxt_enable_feature_flag_name, enable_keypoint_detection) -> None:
        if enable_keypoint_detection:
            fxt_enable_feature_flag_name(FEATURE_FLAG_KEYPOINT_DETECTION)
        register_model_template(request, type(None), "counting", "COUNTING", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test MongoDB mapper ",
            description="test_Project_mapper()",
            model_template_id="counting",
            number_of_videos=0,
            number_of_images=0,
        )[0]
        _, deserialized_project = verify_mongo_mapper(
            entity_to_map=project,
            mapper_class=ProjectToMongo,
            extend_forward_output={"workspace_id": project.workspace_id},
            compare_backward_maps=False,
        )
        assert isinstance(deserialized_project.training_dataset_storage_adapter, ProxyAdapter)
        compare(
            deserialized_project.get_training_dataset_storage(),
            project.get_training_dataset_storage(),
            ignore_eq=True,
        )

    def test_task_graph_mapper(
        self,
        request,
        fxt_model_template_detection,
        fxt_model_template_crop,
        fxt_model_template_classification,
    ) -> None:
        detection_properties = TaskProperties(
            task_family=TaskFamily.VISION,
            task_type=TaskType.DETECTION,
            is_trainable=True,
            is_global=False,
            is_anomaly=False,
        )
        detection_task = TaskNode(
            title="Detect test",
            project_id=ID(),
            task_properties=detection_properties,
            id_=TaskNodeRepo.generate_id(),
        )
        crop_properties = TaskProperties(
            task_family=TaskFamily.FLOW_CONTROL,
            task_type=TaskType.CROP,
            is_trainable=False,
            is_global=False,
            is_anomaly=False,
        )
        crop_task = TaskNode(
            title="Crop test",
            project_id=ID(),
            task_properties=crop_properties,
            id_=TaskNodeRepo.generate_id(),
        )
        classification_properties = TaskProperties(
            task_family=TaskFamily.VISION,
            task_type=TaskType.CLASSIFICATION,
            is_trainable=True,
            is_global=True,
            is_anomaly=False,
        )
        classification_task = TaskNode(
            title="Classification test",
            project_id=ID(),
            task_properties=classification_properties,
            id_=TaskNodeRepo.generate_id(),
        )

        edge_1 = TaskEdge(from_task=detection_task, to_task=crop_task)

        edge_2 = TaskEdge(from_task=crop_task, to_task=classification_task)

        task_graph = TaskGraph()
        task_graph.add_task_edge(edge_1)
        task_graph.add_task_edge(edge_2)

        model_templates = [
            fxt_model_template_detection,
            fxt_model_template_crop,
            fxt_model_template_classification,
        ]

        project = ProjectFactory.create_project_with_task_graph(
            name="test",
            creator_id="",
            description="desc",
            task_graph=task_graph,
            model_templates=model_templates,
        )

        for node in project.tasks:
            assert node in project.task_graph.nodes

        _, deserialized_project = verify_mongo_mapper(
            entity_to_map=project,
            mapper_class=ProjectToMongo,
            extend_forward_output={
                "workspace_id": project.workspace_id,
                "project_id": project.id_,
            },
            compare_backward_maps=False,
        )
        compare(task_graph, deserialized_project.task_graph, ignore_eq=True)
        assert project == deserialized_project

    def test_label_schema_mapper(self, fxt_mongo_id, fxt_empty_project, fxt_label_schema_example_persisted) -> None:
        # Arrange
        label_schema = fxt_label_schema_example_persisted.label_schema
        label_schema.previous_schema_revision_id = fxt_mongo_id(1)
        label_schema.deleted_label_ids = [fxt_label_schema_example_persisted.flowering.id_]
        verify_mongo_mapper(
            entity_to_map=label_schema,
            mapper_class=LabelSchemaToMongo,
            extend_forward_output={
                "workspace_id": fxt_empty_project.workspace_id,
                "project_id": fxt_empty_project.id_,
            },
            compare_forward_maps=False,
        )

    def test_label_group_mapper(self, fxt_mongo_id, fxt_empty_project, fxt_label_schema_example_persisted) -> None:
        label_schema = fxt_label_schema_example_persisted.label_schema
        label_group = label_schema.get_groups()[0]
        verify_mongo_mapper(
            entity_to_map=label_group,
            mapper_class=LabelGroupToMongo,
            project=fxt_empty_project,
        )

    def test_task_node_mapper(self, project_empty) -> None:
        detection_properties = TaskProperties(
            task_family=TaskFamily.VISION,
            task_type=TaskType.DETECTION,
            is_trainable=True,
            is_global=False,
            is_anomaly=False,
        )
        task_node = TaskNode(
            title="Test task",
            task_properties=detection_properties,
            project_id=project_empty.id_,
            id_=TaskNodeRepo.generate_id(),
            ephemeral=False,
        )
        verify_mongo_mapper(
            entity_to_map=task_node,
            mapper_class=TaskNodeToMongo,
            extend_forward_output={
                "workspace_id": project_empty.workspace_id,
                "project_id": project_empty.id_,
            },
        )

    def test_label_mapper(self) -> None:
        label = Label(
            name="Label name",
            domain=Domain.CLASSIFICATION,
            color=Color(red=255, green=100, blue=55, alpha=255),
            hotkey="abcdef",
            is_empty=True,
            id_=LabelRepo.generate_id(),
            is_anomalous=True,
            ephemeral=False,
        )
        verify_mongo_mapper(entity_to_map=label, mapper_class=LabelToMongo)

    def test_scored_label_mapper(self, fxt_classification_labels_persisted, fxt_ote_id, fxt_empty_project) -> None:
        cls_labels = fxt_classification_labels_persisted(fxt_empty_project.identifier)
        scored_label = ScoredLabel(
            label_id=cls_labels[0].id_,
            is_empty=cls_labels[0].is_empty,
            probability=0.5,
            label_source=LabelSource(
                user_id="default_user",
                model_id=fxt_ote_id(1),
                model_storage_id=fxt_ote_id(2),
            ),
        )
        verify_mongo_mapper(
            entity_to_map=scored_label,
            mapper_class=ScoredLabelToMongo,
            project=fxt_empty_project,
        )

    def test_model_storage_mapper(self, request, fxt_mongo_id) -> None:
        model_storage = ModelStorage(
            id_=ModelStorageRepo.generate_id(),
            project_id=fxt_mongo_id(2),
            task_node_id=fxt_mongo_id(4),
            model_template=NullModelTemplate(),
            ephemeral=False,
        )
        verify_mongo_mapper(
            entity_to_map=model_storage,
            mapper_class=ModelStorageToMongo,
            extend_forward_output={
                "workspace_id": fxt_mongo_id(1),
                "project_id": fxt_mongo_id(2),
            },
        )

    def test_performance_mapper(self) -> None:
        performance = Performance(
            score=ScoreMetric(name="Dice score", value=0.7),
            dashboard_metrics=[
                LineMetricsGroup(
                    metrics=[CurveMetric(name="loss", ys=[1, 0.5, 0])],
                    visualization_info=LineChartInfo(name="Loss curve", x_axis_label="Epoch", y_axis_label="Loss"),
                ),
                TextMetricsGroup(
                    metrics=[ScoreMetric(name="overall dice", value=0.8)],
                    visualization_info=TextChartInfo(name="dice score"),
                ),
                BarMetricsGroup(
                    metrics=[
                        ScoreMetric(name="label1", value=0.7),
                        ScoreMetric(name="label2", value=0.6),
                    ],
                    visualization_info=BarChartInfo(
                        name="Dice per label",
                    ),
                ),
                BarMetricsGroup(
                    metrics=[
                        ScoreMetric(name="label", value=0.7),
                        ScoreMetric(name="label2", value=0.6),
                    ],
                    visualization_info=BarChartInfo(
                        name="dummy radial bar chart",
                        visualization_type=VisualizationType.RADIAL_BAR,
                    ),
                ),
                MatrixMetricsGroup(
                    metrics=[
                        MatrixMetric(name="label", matrix_values=np.zeros((2, 2))),
                        MatrixMetric(name="label", matrix_values=np.zeros((2, 2))),
                    ],
                    visualization_info=MatrixChartInfo(
                        name="dummy radial bar chart",
                        header="matrix chart header",
                        row_header="matrix row header",
                        column_header="matrix column header",
                    ),
                ),
            ],
        )

        multi_score_performance = MultiScorePerformance(
            primary_score=ScoreMetric(name="Dice score", value=0.7),
            additional_scores=[
                ScoreMetric(name="Precision", value=0.6),
                ScoreMetric(name="Recall", value=0.5),
            ],
            dashboard_metrics=performance.dashboard_metrics,
        )

        anomaly_performance = AnomalyLocalizationPerformance(
            local_score=ScoreMetric(name="Dice score", value=0.75),
            global_score=ScoreMetric(name="F1 score", value=0.85),
            dashboard_metrics=performance.dashboard_metrics,
        )

        mongo_performance = PerformanceToMongo.forward(performance)
        performance_from_mongo = PerformanceToMongo.backward(mongo_performance)
        mongo_performance_back = PerformanceToMongo.forward(performance_from_mongo)
        compare(mongo_performance, mongo_performance_back, ignore_eq=True)

        verify_mongo_mapper(entity_to_map=performance, mapper_class=PerformanceToMongo)
        verify_mongo_mapper(entity_to_map=multi_score_performance, mapper_class=PerformanceToMongo)
        verify_mongo_mapper(entity_to_map=anomaly_performance, mapper_class=PerformanceToMongo)

    def test_matrix_mapper(self) -> None:
        labels = ["one", "two", "three"]
        matrix_metric = MatrixMetric(
            name="confusion",
            matrix_values=np.array([[3, 0, 1], [1, 2, 0], [3, 2, 5]]),
            row_labels=labels,
            column_labels=labels,
            normalize=True,
        )
        matrix_visualisation_info = MatrixChartInfo(
            name="Loss curve",
            header="Confusion matrix",
            row_header="Predicted label",
            column_header="True label",
        )
        performance = Performance(
            score=ScoreMetric(name="Accuracy", value=0.7),
            dashboard_metrics=[
                MatrixMetricsGroup(
                    metrics=[matrix_metric],
                    visualization_info=matrix_visualisation_info,
                )
            ],
        )

        verify_mongo_mapper(entity_to_map=performance, mapper_class=PerformanceToMongo)

    def test_numpy_mapper(self) -> None:
        numpy_array = np.random.randint(10, size=(3, 5, 7))  # Generate random 3x5x7 array with values between 0 and 9

        mongo_numpy_array = NumpyToMongo.forward(numpy_array)
        assert len(mongo_numpy_array["array_values"]) == np.prod(mongo_numpy_array["array_shape"])
        np.testing.assert_array_equal(mongo_numpy_array["array_shape"], numpy_array.shape)
        np.testing.assert_array_equal(mongo_numpy_array["array_values"], numpy_array.reshape(-1))

        reconstructed_numpy_array = NumpyToMongo.backward(mongo_numpy_array)
        np.testing.assert_array_equal(reconstructed_numpy_array, numpy_array)

    def test_dataset_storage_mapper(self, fxt_dataset_storage_persisted) -> None:
        verify_mongo_mapper(
            entity_to_map=fxt_dataset_storage_persisted,
            mapper_class=DatasetStorageToMongo,
            extend_forward_output={
                "workspace_id": fxt_dataset_storage_persisted.workspace_id,
                "project_id": fxt_dataset_storage_persisted.project_id,
            },
        )

    def test_video_identifier_mapper(self, request, fxt_random_annotated_video_factory) -> None:
        video_identifier = VideoIdentifier(video_id=VideoRepo.generate_id())
        verify_mongo_mapper(entity_to_map=video_identifier, mapper_class=VideoIdentifierToMongo)

    def test_suspended_annotation_scenes_descriptor_mapper(self, request, fxt_mongo_id) -> None:
        desc = SuspendedAnnotationScenesDescriptor(
            id_=fxt_mongo_id(0),
            project_id=fxt_mongo_id(1),
            dataset_storage_id=fxt_mongo_id(2),
            scenes_ids=(fxt_mongo_id(3), fxt_mongo_id(4)),
        )
        verify_mongo_mapper(
            entity_to_map=desc,
            mapper_class=SuspendedAnnotationScenesDescriptorToMongo,
            extend_forward_output={
                "project_id": str(desc.project_id),
                "dataset_storage_id": str(desc.dataset_storage_id),
            },
        )

    def test_model_test_result_mapper(self, fxt_model_test_result, fxt_empty_project, fxt_model) -> None:
        ds1 = fxt_model_test_result.get_dataset_storages()
        model_test_result_mapped = ModelTestResultToMongo.forward(instance=fxt_model_test_result)
        # workspace_id and project_id are mapped indirectly from the session repo base class
        model_test_result_mapped["workspace_id"] = fxt_empty_project.workspace_id
        model_test_result_mapped["project_id"] = fxt_empty_project.id_
        model_test_result_unmapped = ModelTestResultToMongo.backward(instance=model_test_result_mapped)
        model_test_result_remapped = ModelTestResultToMongo.forward(model_test_result_unmapped)
        model_test_result_remapped["workspace_id"] = fxt_empty_project.workspace_id
        model_test_result_remapped["project_id"] = fxt_empty_project.id_

        assert fxt_model_test_result == model_test_result_unmapped
        compare(model_test_result_mapped, model_test_result_remapped, ignore_eq=True)

        # Check that all adapter members are equal before and after mapping
        with (
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as patched_get_model,
            patch.object(
                DatasetStorageRepo,
                "get_by_id",
                return_value=ds1,
            ) as patched_get_dataset_storage,
        ):
            assert fxt_model_test_result.model_storage_id == model_test_result_unmapped.model_storage_id
            assert fxt_model_test_result.get_model() == model_test_result_unmapped.get_model()
            assert fxt_model_test_result.get_dataset_storages() == model_test_result_unmapped.get_dataset_storages()

        patched_get_dataset_storage.assert_has_calls(
            [
                call(fxt_model_test_result.dataset_storage_ids[0]),
            ]
        )
        patched_get_model.assert_has_calls(
            [
                call(fxt_model_test_result.model_id),
            ]
        )

    def test_media_score_mapper(self, fxt_media_score_2) -> None:
        serialized_entity = MediaScoreToMongo.forward(instance=fxt_media_score_2)
        deserialized_entity = MediaScoreToMongo.backward(instance=serialized_entity)
        reserialized_entity = MediaScoreToMongo.forward(instance=deserialized_entity)

        compare(fxt_media_score_2, deserialized_entity)
        # sort because mapping a set() to an array does not guarantee the order
        serialized_entity["scores"].sort(key=lambda d: d["name"])
        reserialized_entity["scores"].sort(key=lambda d: d["name"])
        compare(serialized_entity, reserialized_entity)

    def test_active_model_state_mapper(self, fxt_empty_project, fxt_model_storage_classification) -> None:
        model_storage = fxt_model_storage_classification
        active_model_state = ActiveModelState(
            task_node_id=TaskNodeRepo.generate_id(),
            active_model_storage=model_storage,
            ephemeral=False,
        )
        with patch.object(ModelStorageRepo, "get_by_id", return_value=model_storage) as mock_get_model_storage:
            verify_mongo_mapper(
                entity_to_map=active_model_state,
                mapper_class=ActiveModelStateToMongo,
                project=fxt_empty_project,
            )
            mock_get_model_storage.assert_called()

    def test_evaluation_result_mapper(self, request, fxt_model) -> None:
        register_model_template(request, type(None), "counting", "COUNTING", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test MongoDB mapper ",
            description="test_evaluation_result_mapper()",
            model_template_id="counting",
            number_of_videos=0,
            number_of_images=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        _, train_dataset = generate_training_dataset_of_all_annotated_media_in_project(project)
        analyse_dataset = generate_inference_dataset_of_all_media_in_project(project)
        performance = Performance(score=ScoreMetric(value=1.0, name="name"))
        evaluation_result = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=project.identifier,
            model_storage_id=fxt_model.model_storage.id_,
            model_id=fxt_model.id_,
            dataset_storage_id=project.training_dataset_storage_id,
            ground_truth_dataset=train_dataset.id_,
            prediction_dataset=analyse_dataset.id_,
            performance=performance,
        )

        assert performance == evaluation_result.performance

        extend_forward_output = {
            "workspace_id": IDToMongo.forward(project.workspace_id),
            "project_id": IDToMongo.forward(project.id_),
        }
        _, deserialized_evaluation_result = verify_mongo_mapper(
            entity_to_map=evaluation_result,
            mapper_class=EvaluationResultToMongo,
            dataset_storage=dataset_storage,
            extend_forward_output=extend_forward_output,
            compare_backward_maps=True,
        )

    def test_annotation_scene_mapper(self, fxt_empty_project) -> None:
        rectangle_annotation = Annotation(Rectangle(0, 0, 1, 1), labels=[])
        ellipse_annotation = Annotation(Ellipse(0, 0, 1, 1), labels=[])
        polygon_annotation = Annotation(Polygon([Point(2, 2), Point(3, 3), Point(4, 4)]), labels=[])
        keypoint_annotation = Annotation(Keypoint(x=1, y=1, is_visible=True), labels=[])
        annotations = [
            rectangle_annotation,
            ellipse_annotation,
            polygon_annotation,
            keypoint_annotation,
        ]
        image_identifier = ImageIdentifier(ImageRepo.generate_id())
        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=image_identifier,
            media_height=1,
            media_width=1,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id="test",
            annotations=annotations,
            invalid_task_ids=[AnnotationSceneRepo.generate_id()],
            task_id=AnnotationSceneRepo.generate_id(),
            ephemeral=False,
        )

        verify_mongo_mapper(
            entity_to_map=annotation_scene,
            mapper_class=AnnotationSceneToMongo,
            project=fxt_empty_project,
        )

    def test_annotation_scene_state_mapper(self, fxt_mongo_id) -> None:
        annotation_scene_state = AnnotationSceneState(
            media_identifier=ImageIdentifier(image_id=ID(fxt_mongo_id(0))),
            annotation_scene_id=fxt_mongo_id(1),
            annotation_state_per_task={
                fxt_mongo_id(2): AnnotationState.ANNOTATED,
                fxt_mongo_id(3): AnnotationState.PARTIALLY_ANNOTATED,
                fxt_mongo_id(4): AnnotationState.NONE,
            },
            id_=fxt_mongo_id(5),
            unannotated_rois={
                fxt_mongo_id(6): [
                    fxt_mongo_id(7),
                    fxt_mongo_id(8),
                ],
                fxt_mongo_id(9): [
                    fxt_mongo_id(10),
                    fxt_mongo_id(11),
                ],
            },
            labels_to_revisit_per_annotation={
                fxt_mongo_id(12): [fxt_mongo_id(15), fxt_mongo_id(16)],
                fxt_mongo_id(13): [fxt_mongo_id(17)],
                fxt_mongo_id(14): [],
            },
            labels_to_revisit_full_scene=[fxt_mongo_id(18), fxt_mongo_id(19)],
        )

        annotation_scene_state_serialized = AnnotationSceneStateToMongo.forward(annotation_scene_state)
        annotation_scene_state_deserialized = AnnotationSceneStateToMongo.backward(annotation_scene_state_serialized)
        annotation_scene_state_reserialized = AnnotationSceneStateToMongo.forward(annotation_scene_state_deserialized)
        # Because AnnotationSceneState internally contains sets that get serialized into
        # lists, here we sort these fields to ensure a predictable order of the elements
        # for comparison purposes, otherwise the test would be flaky.
        annotation_scene_state_serialized["labels_to_revisit_full_scene"].sort()
        annotation_scene_state_reserialized["labels_to_revisit_full_scene"].sort()

        assert annotation_scene_state == annotation_scene_state_deserialized
        compare(
            annotation_scene_state_serialized,
            annotation_scene_state_reserialized,
            ignore_eq=True,
        )

    def test_dataset_item_mapper(
        self,
        fxt_ote_id,
        fxt_dataset_storage_persisted,
        fxt_image_entity,
        fxt_annotation_scene,
    ) -> None:
        image = fxt_image_entity
        ann_scene = fxt_annotation_scene
        label_ids = list(ann_scene.get_label_ids())
        ignored_label_ids = label_ids[:1]
        AnnotationSceneCache()._shared_annotations[ann_scene.id_] = ann_scene
        dataset_item = DatasetItem(
            id_=fxt_ote_id(2),
            media=image,
            annotation_scene=ann_scene,
            roi=ann_scene.annotations[0],
            metadata=[],
            subset=Subset.TRAINING,
            ignored_label_ids=ignored_label_ids,
        )
        with (
            patch.object(ImageRepo, "get_by_id", return_value=image) as mock_image_get_by_id,
        ):
            _, deserialized_item = verify_mongo_mapper(
                entity_to_map=dataset_item,
                mapper_class=DatasetItemToMongo,
                dataset_storage=fxt_dataset_storage_persisted,
                extend_forward_output={
                    "organization_id": IDToMongo.forward(DEFAULT_ORGANIZATION_ID),
                    "workspace_id": IDToMongo.forward(fxt_dataset_storage_persisted.workspace_id),
                    "project_id": IDToMongo.forward(fxt_dataset_storage_persisted.project_id),
                    "dataset_storage_id": IDToMongo.forward(fxt_dataset_storage_persisted.id_),
                },
            )

        mock_image_get_by_id.assert_called_once_with(image.media_identifier.media_id)

    def test_dataset_mapper(self, fxt_ote_id, fxt_dataset_storage) -> None:
        dataset = Dataset(
            id=fxt_ote_id(1),
            purpose=DatasetPurpose.TEMPORARY_DATASET,
            mutable=False,
            label_schema_id=fxt_ote_id(2),
        )

        with patch.object(_DatasetItemRepo, "get_all_docs", return_value=[]):
            verify_mongo_mapper(
                entity_to_map=dataset,
                mapper_class=DatasetToMongo,
                dataset_storage=fxt_dataset_storage,
            )

    def test_image_mapper(self, request) -> None:
        register_model_template(request, type(None), "counting", "COUNTING", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test MongoDB mapper ",
            description="test_Image_mapper()",
            model_template_id="counting",
            number_of_images=1,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        image_repo = ImageRepo(dataset_storage.identifier)
        image = list(image_repo.get_all())[0]
        verify_mongo_mapper(entity_to_map=image, mapper_class=ImageToMongo)

    def test_video_mapper(self, fxt_video_project, fxt_random_annotated_video_factory) -> None:
        project: Project = fxt_video_project
        video, _, _, _, _, _, _ = fxt_random_annotated_video_factory(project=project)
        verify_mongo_mapper(entity_to_map=video, mapper_class=VideoToMongo)

    def test_float_metadata_mapper(self) -> None:
        float_metadata = FloatMetadata(
            name="foo",
            float_type=FloatType.EMBEDDING_VALUE,
            value=3.5,
        )

        verify_mongo_mapper(entity_to_map=float_metadata, mapper_class=FloatMetadataToMongo)

    def test_tensor_mapper(self, request, fxt_dataset_storage) -> None:
        ds_identifier = fxt_dataset_storage.identifier
        tensor_binary_repo = MetadataRepo(ds_identifier).tensor_binary_repo
        tensor_name = "dummy_tensor.npz"
        tensor_numpy = np.zeros((10, 10, 3)).astype(np.uint8)
        buffer = io.BytesIO()
        np.savez(buffer, array=tensor_numpy)
        data = buffer.getvalue()

        tensor_filename = tensor_binary_repo.save(
            dst_file_name=tensor_name,
            data_source=data,
        )
        request.addfinalizer(lambda: tensor_binary_repo.delete_by_filename(filename=tensor_filename))
        tensor_adapter = TensorAdapter(
            data_source=tensor_binary_repo,
            binary_filename=tensor_filename,
            shape=tensor_numpy.shape,
        )
        tensor = Tensor(name=tensor_name, tensor_adapter=tensor_adapter)

        verify_mongo_mapper(
            entity_to_map=tensor,
            mapper_class=TensorToMongo,
            backward_parameters=TensorMapperBackwardParameters(tensor_binary_repo=tensor_binary_repo),
        )

    def test_metadata_item_mapper(
        self, fxt_dataset_storage_persisted, fxt_ote_id, fxt_image_identifier, fxt_model
    ) -> None:
        metadata_repo = MetadataRepo(fxt_dataset_storage_persisted.identifier)
        float_metadata = FloatMetadata(
            name="foo",
            float_type=FloatType.EMBEDDING_VALUE,
            value=3.5,
        )
        metadata_item = MetadataItem(
            id=fxt_ote_id(10),
            data=float_metadata,
            dataset_item_id=fxt_ote_id(11),
            media_identifier=fxt_image_identifier,
            model=fxt_model,
        )

        with (
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model.model_storage),
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model),
        ):
            verify_mongo_mapper(
                entity_to_map=metadata_item,
                mapper_class=MetadataItemToMongo,
                backward_parameters=MetadataItemMapperBackwardParameters(
                    dataset_storage_identifier=fxt_dataset_storage_persisted.identifier,
                    tensor_binary_repo=metadata_repo.tensor_binary_repo,
                ),
            )

    def test_project_performance_mapper(self) -> None:
        project_performance = ProjectPerformance(
            score=0.72,
            task_performances=[
                TaskPerformance(
                    task_node_id=TaskNodeRepo.generate_id(),
                    score=TaskPerformanceScore(value=0.89, metric_type="f-measure"),
                ),
                GlobalLocalTaskPerformance(
                    task_node_id=TaskNodeRepo.generate_id(),
                    global_score=TaskPerformanceScore(value=0.45, metric_type="f-measure"),
                    local_score=TaskPerformanceScore(value=0.56, metric_type="dice average"),
                ),
            ],
        )
        verify_mongo_mapper(entity_to_map=project_performance, mapper_class=ProjectPerformanceToMongo)

    def test_training_framework_mapper(self, fxt_training_framework):
        verify_mongo_mapper(entity_to_map=fxt_training_framework, mapper_class=TrainingFrameworkToMongo)

    def test_model_mapper(self, fxt_empty_project, fxt_dataset, fxt_training_framework) -> None:
        model_storage = ModelStorage(
            id_=ModelStorageRepo.generate_id(),
            project_id=fxt_empty_project.id_,
            task_node_id=ID(),
            model_template=NullModelTemplate(),
        )
        performance = Performance(
            score=ScoreMetric(name="Dice score", value=0.7),
            dashboard_metrics=[
                LineMetricsGroup(
                    metrics=[CurveMetric(name="loss", ys=[1, 0.5, 0])],
                    visualization_info=LineChartInfo(name="Loss curve", x_axis_label="Epoch", y_axis_label="Loss"),
                )
            ],
        )
        previous_model = Model(
            project=fxt_empty_project,
            model_storage=model_storage,
            train_dataset=fxt_dataset,
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            performance=performance,
            data_source_dict={"inference_model.bin": b"Previous model data"},
            training_framework=fxt_training_framework,
            precision=[ModelPrecision.FP32],
        )
        model = Model(
            project=fxt_empty_project,
            model_storage=model_storage,
            train_dataset=fxt_dataset,
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            performance=performance,
            previous_trained_revision=previous_model,
            tags=["test"],
            data_source_dict={"inference_model.bin": b"Model data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.TRAINED_NO_STATS,
            model_format=ModelFormat.ONNX,
            has_xai_head=True,
            training_duration=100,
            precision=[ModelPrecision.INT4, ModelPrecision.INT8],
            latency=6,
            fps_throughput=6,
            target_device_type="CPU",
            optimization_type=ModelOptimizationType.POT,
            optimization_objectives={"test": "test"},
            performance_improvement={"test": 1.0},
            model_size_reduction=1.0,
            size=100,
            version=6,
            ephemeral=False,
            purge_info=ModelPurgeInfo(
                is_purged=True,
                purge_time=now(),
                user_uid="0c0ee1b6-7f03-48eb-b1b5-c2598c48047d",
            ),
        )
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
            patch.object(DatasetRepo, "get_by_id", return_value=fxt_dataset),
        ):
            verify_mongo_mapper(
                entity_to_map=model,
                mapper_class=ModelToMongo,
                extend_forward_output={
                    "workspace_id": str(model_storage.workspace_id),
                    "project_id": str(model_storage.project_id),
                    "model_storage_id": str(model_storage.id_),
                },
            )

    def test_training_revision_mapper(self, fxt_dataset_item) -> None:
        ds_item = fxt_dataset_item()

        expected_result = {
            "_id": ObjectId(ds_item.id_),
            "media_identifier": {
                "media_id": ObjectId(ds_item.media.id_),
                "type": "image",
            },
            "roi": {
                "_id": ObjectId(ds_item.roi_id),
                "labels": [],
                "shape": {
                    "area_percentage": 0,
                    "area_pixel": 0.0,
                    "modification_date": ANY,
                    "type": "RECTANGLE",
                    "x1": 0.0,
                    "x2": 1.0,
                    "y1": 0.0,
                    "y2": 1.0,
                },
            },
            "subset": str(ds_item.subset),
            "media_name": ds_item.media.name,
            "media_extension": ds_item.media.extension.name,
            "media_width": ds_item.media.width,
            "media_height": ds_item.media.height,
            "upload_date": ANY,
            "uploader_id": ds_item.media.uploader_id,
            "size": 100,
            "user_name": ds_item.annotation_scene.last_annotator_id,
            "annotation_scene_id": ObjectId(ds_item.annotation_scene.id_),
            "annotations": [
                [
                    {
                        "shape": {
                            "area_percentage": 0.03125,
                            "area_pixel": 32.0,
                            "modification_date": ANY,
                            "type": "RECTANGLE",
                        }
                    }
                ]
            ],
            "label_ids": [
                ObjectId(label_id) for label_id in ds_item.annotation_scene.get_label_ids(include_empty=True)
            ],
            "creation_date": ANY,
        }

        result = TrainingRevisionToMongo.forward(ds_item)

        compare(result, expected_result)

    def test_dataset_storage_filter_mapper(self, fxt_dataset_storage_filter_data) -> None:
        verify_mongo_mapper(
            entity_to_map=fxt_dataset_storage_filter_data,
            mapper_class=DatasetStorageFilterDataToMongo,
        )

    def test_video_annotation_range_mapper(self, fxt_ote_id) -> None:
        range_labels = [
            RangeLabels(start_frame=0, end_frame=7, label_ids=[ID("A")]),
            RangeLabels(start_frame=8, end_frame=10, label_ids=[ID("A"), ID("B")]),
            RangeLabels(start_frame=11, end_frame=12, label_ids=[ID("A"), ID("B"), ID("C")]),
            RangeLabels(start_frame=13, end_frame=76, label_ids=[ID("B"), ID("C")]),
            RangeLabels(start_frame=77, end_frame=77, label_ids=[ID("B")]),
            RangeLabels(start_frame=95, end_frame=100, label_ids=[ID("B")]),
        ]
        video_annotation_range = VideoAnnotationRange(
            video_id=fxt_ote_id(1),
            range_labels=range_labels,
            id_=fxt_ote_id(2),
        )
        verify_mongo_mapper(
            entity_to_map=video_annotation_range,
            mapper_class=VideoAnnotationRangeToMongo,
        )

    def test_annotation_template_mapper(self, fxt_ote_id) -> None:
        annotation_template = AnnotationTemplate(
            id_=fxt_ote_id(1),
            name="test_name",
            value="test_value",
        )
        verify_mongo_mapper(entity_to_map=annotation_template, mapper_class=AnnotationTemplateToMongo)

    def test_keypoint_structure_mapper(self) -> None:
        keypoint_structure = KeypointStructure(
            edges=[
                KeypointEdge(node_1=ID("head"), node_2=ID("back")),
                KeypointEdge(node_1=ID("back"), node_2=ID("tail")),
            ],
            positions=[
                KeypointPosition(node=ID("head"), x=0, y=0),
                KeypointPosition(node=ID("back"), x=0.5, y=0.5),
                KeypointPosition(node=ID("tail"), x=1, y=1),
            ],
        )
        verify_mongo_mapper(entity_to_map=keypoint_structure, mapper_class=KeypointStructureToMongo)

    def test_id_mapper(self) -> None:
        empty_ = ID()
        uuid_ = ID("00000000-0000-0000-0000-000000000001")
        id_ = ID("63B183D00000000000000001")
        str_ = ID("str_id")
        dig_ = ID("1234")

        mapped_empty_ = IDToMongo.forward(empty_)
        mapped_uuid_ = IDToMongo.forward(uuid_)
        mapped_id_ = IDToMongo.forward(id_)
        mapped_str_ = IDToMongo.forward(str_)
        mapped_dig_ = IDToMongo.forward(dig_)

        assert mapped_empty_ == ""
        assert mapped_uuid_ == UUID("00000000-0000-0000-0000-000000000001")
        assert mapped_id_ == ObjectId("63B183D00000000000000001")
        assert mapped_str_ == "str_id"
        assert mapped_dig_ == ObjectId("000000000000000000001234")

        unmapped_empty = IDToMongo.backward(mapped_empty_)
        unmapped_uuid_ = IDToMongo.backward(mapped_uuid_)
        unmapped_id_ = IDToMongo.backward(mapped_id_)
        unmapped_str_ = IDToMongo.backward(mapped_str_)
        unmapped_dig_ = IDToMongo.backward(mapped_dig_)

        assert unmapped_empty == empty_
        assert unmapped_uuid_ == uuid_
        assert unmapped_id_ == id_
        assert unmapped_str_ == str_
        assert unmapped_dig_ == ID("000000000000000000001234")

    def test_session_mapper(self) -> None:
        session = Session(
            organization_id=ID("12345678-0000-0000-0000-000000000001"),
            workspace_id=ID("00000000-1234-5678-0000-000000000001"),
        )
        verify_mongo_mapper(entity_to_map=session, mapper_class=SessionToMongo)

    def test_session_mapper_backward_compatibility(self) -> None:
        session_doc = {
            "organization_id": "12345678-0000-0000-0000-000000000001",
            "workspace_id": "00000000-1234-5678-0000-000000000001",
        }
        session = SessionToMongo.backward(session_doc)
        assert session == Session(
            organization_id=ID("12345678-0000-0000-0000-000000000001"),
            workspace_id=ID("00000000-1234-5678-0000-000000000001"),
        )
