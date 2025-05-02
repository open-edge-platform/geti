# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest

from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.annotation_scene_state import AnnotationSceneState, AnnotationState, NullAnnotationSceneState
from iai_core_py.entities.label import Domain, Label
from iai_core_py.entities.label_schema import LabelGroup, LabelSchema
from iai_core_py.entities.model_template import TaskFamily, TaskType
from iai_core_py.entities.project import Project
from iai_core_py.entities.scored_label import ScoredLabel
from iai_core_py.entities.shapes import Rectangle
from iai_core_py.entities.task_graph import TaskGraph
from iai_core_py.entities.task_node import TaskNode, TaskProperties
from iai_core_py.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, VideoRepo
from iai_core_py.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core_py.utils.identifier_factory import IdentifierFactory

from geti_types import ID, ImageIdentifier, VideoFrameIdentifier, VideoIdentifier

MEDIA_HEIGHT = 480
MEDIA_WIDTH = 640


def do_nothing(self, *args, **kwargs) -> None:
    return None


@pytest.fixture
def fxt_detection_label_schema(fxt_mongo_id):
    label_schema = LabelSchema(fxt_mongo_id(14))
    label_schema.add_group(
        LabelGroup(
            name="default detection",
            labels=[
                Label(name="detection label", domain=Domain.DETECTION, id_=fxt_mongo_id(1)),
                Label(name="Empty detection label", domain=Domain.DETECTION, is_empty=True, id_=fxt_mongo_id(7)),
            ],
        )
    )
    yield label_schema


@pytest.fixture
def fxt_detection_node(fxt_mongo_id):
    task_properties = TaskProperties(
        task_family=TaskFamily.VISION,
        task_type=TaskType.DETECTION,
        is_trainable=True,
        is_global=False,
        is_anomaly=False,
    )
    yield TaskNode(
        title="Object detection (MOCK)",
        project_id=ID(),
        task_properties=task_properties,
        id_=ID(fxt_mongo_id(2)),
    )


@pytest.fixture
def fxt_segmentation_label_schema(fxt_mongo_id):
    label_schema = LabelSchema(id_=fxt_mongo_id(13))
    label_schema.add_group(
        LabelGroup(
            name="default segmentation",
            labels=[Label(name="segmentation label", domain=Domain.SEGMENTATION, id_=fxt_mongo_id(3))],
        )
    )
    yield label_schema


@pytest.fixture
def fxt_segmentation_node(fxt_mongo_id):
    task_properties = TaskProperties(
        task_family=TaskFamily.VISION,
        task_type=TaskType.SEGMENTATION,
        is_trainable=True,
        is_global=False,
        is_anomaly=False,
    )
    yield TaskNode(
        title="Object detection (MOCK)",
        project_id=ID(),
        task_properties=task_properties,
        id_=ID(fxt_mongo_id(4)),
    )


@pytest.fixture
def fxt_classification_label_schema(fxt_mongo_id):
    label_schema = LabelSchema(id_=fxt_mongo_id(12))
    label_schema.add_group(
        LabelGroup(
            name="default classification",
            labels=[Label(name="classification label", domain=Domain.CLASSIFICATION, id_=fxt_mongo_id(5))],
        )
    )
    yield label_schema


@pytest.fixture
def fxt_classification_node(fxt_mongo_id):
    task_properties = TaskProperties(
        task_family=TaskFamily.VISION,
        task_type=TaskType.CLASSIFICATION,
        is_trainable=True,
        is_global=True,
        is_anomaly=False,
    )
    yield TaskNode(
        title="Object detection (MOCK)",
        project_id=ID(),
        task_properties=task_properties,
        id_=ID(fxt_mongo_id(6)),
    )


@pytest.fixture
def fxt_anomaly_segmentation_label_schema(fxt_mongo_id):
    label_schema = LabelSchema(id_=fxt_mongo_id(11))
    label_schema.add_group(
        LabelGroup(
            name="default anomaly_segmentation",
            labels=[
                Label(name="normal", domain=Domain.ANOMALY_SEGMENTATION, id_=fxt_mongo_id(1), is_anomalous=False),
                Label(name="anomalous", domain=Domain.ANOMALY_SEGMENTATION, id_=fxt_mongo_id(7), is_anomalous=True),
            ],
        )
    )
    yield label_schema


@pytest.fixture(scope="function")
def fxt_anomaly_segmentation_node(fxt_mongo_id):
    task_properties = TaskProperties(
        task_family=TaskFamily.VISION,
        task_type=TaskType.ANOMALY_SEGMENTATION,
        is_trainable=True,
        is_global=False,
        is_anomaly=True,
    )
    yield TaskNode(
        title="Anomaly Segmentation (MOCK)",
        project_id=ID(),
        task_properties=task_properties,
        id_=ID(fxt_mongo_id(102)),
    )


@pytest.fixture
def fxt_anomaly_segmentation_project(
    fxt_mongo_id,
    fxt_anomaly_segmentation_node,
    fxt_dataset_storage,
):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_anomaly_segmentation_node)
    yield Project(
        name="test_anomaly_segmentation_project",
        creator_id="",
        description="Dummy detection->classification project",
        dataset_storages=[fxt_dataset_storage],
        task_graph=task_graph,
        id=fxt_mongo_id(103),
    )


@pytest.fixture
def fxt_pipeline_det_cls_project(
    fxt_mongo_id,
    fxt_detection_node,
    fxt_classification_node,
    fxt_dataset_storage,
):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_detection_node)
    task_graph.add_node(fxt_classification_node)
    yield Project(
        name="test_det_cls_project",
        creator_id="",
        description="Dummy detection->classification project",
        dataset_storages=[fxt_dataset_storage],
        task_graph=task_graph,
        id=fxt_mongo_id(100),
    )


@pytest.fixture
def fxt_pipeline_det_seg_project(
    fxt_mongo_id,
    fxt_detection_node,
    fxt_segmentation_node,
    fxt_dataset_storage,
):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_detection_node)
    task_graph.add_node(fxt_segmentation_node)
    yield Project(
        name="test_det_seg_project",
        creator_id="",
        description="Dummy detection->segmentation project",
        dataset_storages=[fxt_dataset_storage],
        task_graph=task_graph,
        id=fxt_mongo_id(101),
    )


@pytest.fixture
def fxt_node_to_schema(
    fxt_classification_node,
    fxt_classification_label_schema,
    fxt_detection_node,
    fxt_detection_label_schema,
    fxt_segmentation_node,
    fxt_segmentation_label_schema,
    fxt_anomaly_segmentation_node,
    fxt_anomaly_segmentation_label_schema,
):
    def task_node_to_schema(task_id: ID) -> LabelSchema:
        if task_id == fxt_classification_node.id_:
            return fxt_classification_label_schema
        if task_id == fxt_detection_node.id_:
            return fxt_detection_label_schema
        if task_id == fxt_segmentation_node.id_:
            return fxt_segmentation_label_schema
        if task_id == fxt_anomaly_segmentation_node.id_:
            return fxt_anomaly_segmentation_label_schema
        raise ValueError(f"Cannot map task with id {task_id} to a label schema")

    yield task_node_to_schema


class TestAnnotationSceneStateHelper:
    def test_compute_annotation_state_local_to_local_unannotated(
        self,
        fxt_mongo_id,
        fxt_pipeline_det_seg_project,
        fxt_detection_node,
        fxt_segmentation_node,
        fxt_node_to_schema,
    ) -> None:
        """
        <b>Description:</b>
        Checks that the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes for a detection to segmentation project.

        <b>Input data:</b>
        Task graph with a detection and segmentation node. Each node has 1 label.

        <b>Expected results:</b>
        Test passes if the AnnotationSceneStateHelper correctly computes unannotated
        states of annotation scenes.

        <b>Steps</b>
        1. Create a task graph with a detection and segmentation node, and a media
        identifier
        2. Create an AnnotationScene without annotations
        3. Assert that the annotation scene state helper finds AnnotationState NONE for
        both tasks, and that the lists of unannotated ROIs are empty
        """
        media_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id()))

        unannotated_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=MEDIA_HEIGHT,
            media_width=MEDIA_WIDTH,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[],
        )
        with patch(
            "iai_core_py.utils.annotation_scene_state_helper.LabelSchemaRepo.get_latest_view_by_task",
            new=lambda self, task_node_id: fxt_node_to_schema(task_node_id),
        ):
            unannotated_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                project=fxt_pipeline_det_seg_project,
                annotation_scene=unannotated_scene,
            )
        assert unannotated_state.state_per_task == {
            fxt_detection_node.id_: AnnotationState.NONE,
            fxt_segmentation_node.id_: AnnotationState.NONE,
        }
        assert unannotated_state.unannotated_rois == {
            fxt_detection_node.id_: [],
            fxt_segmentation_node.id_: [],
        }

    def test_compute_annotation_state_local_to_local_fully_annotated(
        self,
        fxt_mongo_id,
        fxt_pipeline_det_seg_project,
        fxt_detection_node,
        fxt_detection_label_schema,
        fxt_segmentation_node,
        fxt_segmentation_label_schema,
        fxt_node_to_schema,
    ) -> None:
        """
        <b>Description:</b>
        Checks that the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes for a detection to segmentation project.

        <b>Input data:</b>
        Task graph with a detection and segmentation node. Each node has 1 label.

        <b>Expected results:</b>
        Test passes if the AnnotationSceneStateHelper correctly computes the fully
        annotated states of annotation scenes.

        <b>Steps</b>
        1. Create a task graph with a detection and segmentation node, and a media
        identifier
        2. Create an AnnotationScene with a detection and segmentation annotation,
        that have overlapping shapes.
        3. Assert that the annotation scene state helper finds AnnotationState
        ANNOTATED for both tasks, and that the lists of unannotated ROIs are empty
        """
        detection_label = fxt_detection_label_schema.get_labels(include_empty=False)[0]
        segmentation_label = fxt_segmentation_label_schema.get_labels(include_empty=False)[0]
        media_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id()))

        detection_annotation = Annotation(
            shape=Rectangle(x1=0.3, x2=0.7, y1=0.3, y2=7), labels=[ScoredLabel(label_id=detection_label.id_)]
        )
        segmentation_annotation_in_box = Annotation(
            shape=Rectangle(x1=0.4, x2=0.6, y1=0.4, y2=0.6), labels=[ScoredLabel(label_id=segmentation_label.id_)]
        )
        annotated_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=MEDIA_HEIGHT,
            media_width=MEDIA_WIDTH,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[detection_annotation, segmentation_annotation_in_box],
        )
        with patch(
            "iai_core_py.utils.annotation_scene_state_helper.LabelSchemaRepo.get_latest_view_by_task",
            new=lambda self, task_node_id: fxt_node_to_schema(task_node_id),
        ):
            annotated_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                project=fxt_pipeline_det_seg_project, annotation_scene=annotated_scene
            )
        assert annotated_state.state_per_task == {
            fxt_detection_node.id_: AnnotationState.ANNOTATED,
            fxt_segmentation_node.id_: AnnotationState.ANNOTATED,
        }
        assert annotated_state.unannotated_rois == {
            fxt_detection_node.id_: [],
            fxt_segmentation_node.id_: [],
        }

    def test_compute_annotation_state_local_to_local_partially_annotated(
        self,
        fxt_mongo_id,
        fxt_pipeline_det_seg_project,
        fxt_detection_node,
        fxt_detection_label_schema,
        fxt_segmentation_node,
        fxt_segmentation_label_schema,
        fxt_node_to_schema,
    ) -> None:
        """
        <b>Description:</b>
        Checks that the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes for a detection to segmentation project.

        <b>Input data:</b>
        Task graph with a detection and segmentation node. Each node has 1 label.

        <b>Expected results:</b>
        Test passes if the AnnotationSceneStateHelper correctly computes partially
        annotated states of annotation scenes.

        <b>Steps</b>
        1. Create a task graph with a detection and segmentation node, and a media
        identifier
        2. Create an AnnotationScene with two detection annotations, of which only
        one overlaps with a segmentation annotation's shape.
        3. Assert that the annotation scene state helper finds AnnotationState
        ANNOTATED
        for the detection task and PARTIALLY_ANNOTATED for the segmentation task. Assert
        that the unannotated ROIs are correct: no unannotated ROIs for the first
        task, and the second task has the detection shape as unannotated ROI.
        """
        detection_label = fxt_detection_label_schema.get_labels(include_empty=False)[0]
        segmentation_label = fxt_segmentation_label_schema.get_labels(include_empty=False)[0]
        media_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id()))

        detection_annotation = Annotation(
            shape=Rectangle(x1=0.3, x2=0.7, y1=0.3, y2=7), labels=[ScoredLabel(label_id=detection_label.id_)]
        )

        detection_annotation_2 = Annotation(
            shape=Rectangle(x1=0.1, x2=0.2, y1=0.1, y2=2), labels=[ScoredLabel(label_id=detection_label.id_)]
        )
        segmentation_annotation = Annotation(
            shape=Rectangle(x1=0.1, x2=0.2, y1=0.1, y2=0.2), labels=[ScoredLabel(label_id=segmentation_label.id_)]
        )
        partially_annotated_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=MEDIA_HEIGHT,
            media_width=MEDIA_WIDTH,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[
                detection_annotation,
                detection_annotation_2,
                segmentation_annotation,
            ],
        )
        with patch(
            "iai_core_py.utils.annotation_scene_state_helper.LabelSchemaRepo.get_latest_view_by_task",
            new=lambda self, task_node_id: fxt_node_to_schema(task_node_id),
        ):
            partially_annotated_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                project=fxt_pipeline_det_seg_project,
                annotation_scene=partially_annotated_scene,
            )
        assert partially_annotated_state.state_per_task == {
            fxt_detection_node.id_: AnnotationState.ANNOTATED,
            fxt_segmentation_node.id_: AnnotationState.PARTIALLY_ANNOTATED,
        }
        assert partially_annotated_state.unannotated_rois == {
            fxt_detection_node.id_: [],
            fxt_segmentation_node.id_: [detection_annotation.id_],
        }

    def test_compute_annotation_state_local_to_local_empty_label(
        self,
        fxt_mongo_id,
        fxt_pipeline_det_seg_project,
        fxt_detection_node,
        fxt_detection_label_schema,
        fxt_segmentation_node,
        fxt_segmentation_label_schema,
        fxt_node_to_schema,
    ) -> None:
        """
        <b>Description:</b>
        Checks that the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes for a detection to segmentation project.

        <b>Input data:</b>
        Task graph with a detection and segmentation node. Each node has 1 label.

        <b>Expected results:</b>
        Test passes if the AnnotationSceneStateHelper correctly computes the states
        of annotation scenes when the first task has an empty label annotation.

        <b>Steps</b>
        1. Create a task graph with a detection and segmentation node, and a media
        identifier
        2. Create an Annotationscene with an empty label annotation for the detection
        task
        3. Assert that the annotation scene state helper finds AnnotationState ANNOTATED
        for the detection task and ANNOTATED for the segmentation task. Assert that the
        unannotated ROIs are correct: no unannotated ROIs for both tasks.
        """
        media_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id()))

        empty_label = [label for label in fxt_detection_label_schema.get_labels(include_empty=True) if label.is_empty][
            0
        ]

        detection_annotation_empty = Annotation(
            shape=Rectangle.generate_full_box(), labels=[ScoredLabel(label_id=empty_label.id_, is_empty=True)]
        )
        empty_label_annotated_scene = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=media_identifier,
            media_height=MEDIA_HEIGHT,
            media_width=MEDIA_WIDTH,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[detection_annotation_empty],
        )
        with patch(
            "iai_core_py.utils.annotation_scene_state_helper.LabelSchemaRepo.get_latest_view_by_task",
            new=lambda self, task_node_id: fxt_node_to_schema(task_node_id),
        ):
            empty_label_annotated_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                project=fxt_pipeline_det_seg_project,
                annotation_scene=empty_label_annotated_scene,
            )
        assert empty_label_annotated_state.state_per_task == {
            fxt_detection_node.id_: AnnotationState.ANNOTATED,
            fxt_segmentation_node.id_: AnnotationState.ANNOTATED,
        }
        assert empty_label_annotated_state.unannotated_rois == {
            fxt_detection_node.id_: [],
            fxt_segmentation_node.id_: [],
        }

    def test_compute_annotation_state_local_to_global_unannotated(
        self,
        fxt_mongo_id,
        fxt_pipeline_det_cls_project,
        fxt_detection_node,
        fxt_detection_label_schema,
        fxt_classification_node,
        fxt_classification_label_schema,
        fxt_node_to_schema,
    ) -> None:
        """
        <b>Description:</b>
        Checks that the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes for a task graph with a detection and classification task.

        <b>Input data:</b>
        Task graph with a detection and classification node. Each node has 1 label.

        <b>Expected results:</b>
        Test passes if the AnnotationSceneStateHelper correctly computes unannotated
        states of annotation scenes.

        <b>Steps</b>
        1. Create a task graph with a detection and classification node, and a media
        identifier
        2. Create an AnnotationScene without annotations
        3. Assert that the annotation scene state helper finds AnnotationState NONE for
        both tasks, and that the lists of unannotated ROIs are empty
        """
        media_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id()))

        unannotated_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=MEDIA_HEIGHT,
            media_width=MEDIA_WIDTH,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[],
        )
        with patch(
            "iai_core_py.utils.annotation_scene_state_helper.LabelSchemaRepo.get_latest_view_by_task",
            new=lambda self, task_node_id: fxt_node_to_schema(task_node_id),
        ):
            unannotated_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                project=fxt_pipeline_det_cls_project,
                annotation_scene=unannotated_scene,
            )
        assert unannotated_state.state_per_task == {
            fxt_detection_node.id_: AnnotationState.NONE,
            fxt_classification_node.id_: AnnotationState.NONE,
        }
        assert unannotated_state.unannotated_rois == {
            fxt_detection_node.id_: [],
            fxt_classification_node.id_: [],
        }

    def test_compute_annotation_state_local_to_global_fully_annotated(
        self,
        fxt_mongo_id,
        fxt_pipeline_det_cls_project,
        fxt_detection_node,
        fxt_detection_label_schema,
        fxt_classification_node,
        fxt_classification_label_schema,
        fxt_node_to_schema,
    ) -> None:
        """
        <b>Description:</b>
        Checks that the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes for a task graph with a detection and classification task.

        <b>Input data:</b>
        Task graph with a detection and classification node. Each node has 1 label.

        <b>Expected results:</b>
        Test passes if the AnnotationSceneStateHelper correctly computes annotated
        states of annotation scenes.

        <b>Steps</b>
        1. Create a task graph with a detection and classification node, and a media
        identifier
        2. Create an AnnotationScene with a detection+classification annotation
        3. Assert that the annotation scene state helper finds AnnotationState
        ANNOTATED for both tasks, and that the lists of unannotated ROIs are empty
        """
        detection_label = fxt_detection_label_schema.get_labels(include_empty=False)[0]
        classification_label = fxt_classification_label_schema.get_labels(include_empty=False)[0]
        media_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id()))

        annotation_both_tasks = Annotation(
            shape=Rectangle(x1=0, x2=1, y1=0, y2=1),
            labels=[
                ScoredLabel(label_id=detection_label.id_),
                ScoredLabel(label_id=classification_label.id_),
            ],
        )
        annotated_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=MEDIA_HEIGHT,
            media_width=MEDIA_WIDTH,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[annotation_both_tasks],
        )
        with patch(
            "iai_core_py.utils.annotation_scene_state_helper.LabelSchemaRepo.get_latest_view_by_task",
            new=lambda self, task_node_id: fxt_node_to_schema(task_node_id),
        ):
            annotated_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                project=fxt_pipeline_det_cls_project, annotation_scene=annotated_scene
            )
        assert annotated_state.state_per_task == {
            fxt_detection_node.id_: AnnotationState.ANNOTATED,
            fxt_classification_node.id_: AnnotationState.ANNOTATED,
        }
        assert annotated_state.unannotated_rois == {
            fxt_detection_node.id_: [],
            fxt_classification_node.id_: [],
        }

    def test_compute_annotation_state_local_to_global_partially_annotated(
        self,
        fxt_mongo_id,
        fxt_pipeline_det_cls_project,
        fxt_detection_node,
        fxt_detection_label_schema,
        fxt_classification_node,
        fxt_classification_label_schema,
        fxt_node_to_schema,
    ) -> None:
        """
        <b>Description:</b>
        Checks that the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes for a task graph with a detection and classification task.

        <b>Input data:</b>
        Task graph with a detection and classification node. Each node has 1 label.

        <b>Expected results:</b>
        Test passes if the AnnotationSceneStateHelper correctly computes partially
        annotated states of annotation scenes.

        <b>Steps</b>
        1. Create a task graph with a detection and classification node, and a media
        identifier
        2. Create an AnnotationScene with 2 detection annotations, of which only one
        has a classification label.
        3. Assert that the annotation scene state helper finds AnnotationState ANNOTATED
        for the first task and PARTIALLY_ANNOTATED for the second task. The unannotated
        ROIs must be empty for the first task, and contain the unannotated detection
        box for the second task.
        """
        detection_label = fxt_detection_label_schema.get_labels(include_empty=False)[0]
        classification_label = fxt_classification_label_schema.get_labels(include_empty=False)[0]
        media_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id()))

        annotation_both_tasks = Annotation(
            shape=Rectangle(x1=0, x2=1, y1=0, y2=1),
            labels=[
                ScoredLabel(label_id=detection_label.id_),
                ScoredLabel(label_id=classification_label.id_),
            ],
        )

        annotation_detection_only = Annotation(
            shape=Rectangle(x1=0.2, x2=0.5, y1=0.2, y2=0.5), labels=[ScoredLabel(label_id=detection_label.id_)]
        )
        partially_annotated_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=MEDIA_HEIGHT,
            media_width=MEDIA_WIDTH,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[annotation_both_tasks, annotation_detection_only],
        )
        with patch(
            "iai_core_py.utils.annotation_scene_state_helper.LabelSchemaRepo.get_latest_view_by_task",
            new=lambda self, task_node_id: fxt_node_to_schema(task_node_id),
        ):
            partially_annotated_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                project=fxt_pipeline_det_cls_project,
                annotation_scene=partially_annotated_scene,
            )
        assert partially_annotated_state.state_per_task == {
            fxt_detection_node.id_: AnnotationState.ANNOTATED,
            fxt_classification_node.id_: AnnotationState.PARTIALLY_ANNOTATED,
        }
        assert partially_annotated_state.unannotated_rois == {
            fxt_detection_node.id_: [],
            fxt_classification_node.id_: [annotation_detection_only.id_],
        }

    def test_compute_annotation_state_local_to_global_empty_label(
        self,
        fxt_mongo_id,
        fxt_pipeline_det_cls_project,
        fxt_detection_node,
        fxt_detection_label_schema,
        fxt_classification_node,
        fxt_classification_label_schema,
        fxt_node_to_schema,
    ) -> None:
        """
        <b>Description:</b>
        Checks that the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes for a task graph with a detection and classification task.

        <b>Input data:</b>
        Task graph with a detection and classification node. Each node has 1 label.

        <b>Expected results:</b>
        Test passes if the AnnotationSceneStateHelper correctly computes the states of
        annotation scenes when the first task has an empty label annotation.

        <b>Steps</b>
        1. Create a task graph with a detection and classification node, and a media
        identifier
        2. Create an Annotationscene with an empty label annotation for the detection
        task
        3. Assert that the annotation scene state helper finds AnnotationState
        ANNOTATED for the detection task and ANNOTATED for the classification task. Assert
        that the unannotated ROIs are correct: no unannotated ROIs for both tasks.
        """
        media_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id()))

        empty_label = [label for label in fxt_detection_label_schema.get_labels(include_empty=True) if label.is_empty][
            0
        ]
        detection_annotation_empty = Annotation(
            shape=Rectangle.generate_full_box(), labels=[ScoredLabel(label_id=empty_label.id_, is_empty=True)]
        )
        empty_label_annotated_scene = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=media_identifier,
            media_height=MEDIA_HEIGHT,
            media_width=MEDIA_WIDTH,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[detection_annotation_empty],
        )
        with patch(
            "iai_core_py.utils.annotation_scene_state_helper.LabelSchemaRepo.get_latest_view_by_task",
            new=lambda self, task_node_id: fxt_node_to_schema(task_node_id),
        ):
            empty_label_annotated_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                project=fxt_pipeline_det_cls_project,
                annotation_scene=empty_label_annotated_scene,
            )
        assert empty_label_annotated_state.state_per_task == {
            fxt_detection_node.id_: AnnotationState.ANNOTATED,
            fxt_classification_node.id_: AnnotationState.ANNOTATED,
        }
        assert empty_label_annotated_state.unannotated_rois == {
            fxt_detection_node.id_: [],
            fxt_classification_node.id_: [],
        }

    def test_get_media_per_task_state(
        self,
        fxt_mongo_id,
        fxt_detection_segmentation_chain_project_persisted,
        fxt_video_entity,
    ) -> None:
        """
        <b>Description:</b>
        Check that the query for per-task state of a list of media identifiers works for video frames as well as videos.

        <b>Input data:</b>
        An empty project

        <b>Expected results:</b>
        The AnnotationSceneStateRepo gets the correct annotation states on the media level for videos and frames.

        <b>Steps</b>
        1. Create an empty detection->classification chain project
        2. Initiate AnnotationSceneStateRepo
        3. Create two VideoFrameIdentifier entities and a video entity with the two frame identifiers
        4. Save fully annotated states to the repo for both frames and assert that the frame states are
        correctly loaded
        5. Assert that the video state is loaded as ANNOTATED for both tasks
        6. Change one state to AnnotationState.PARTIALLY_ANNOTATED for the second task and assert that the frame states
         are correct
        7. Assert that the video state for the second task is loaded as AnnotationState.PARTIALLY_ANNOTATED
        8. Update one state to have a label that needs to be revisited
        9. Assert that the video state for both tasks is loaded as AnnotationState.TO_REVISIT
        10. Change both states to AnnotationState.NONE for both tasks and assert that the frame states are correct
        11. Assert that the video state is loaded as AnnotationState.NONE for both tasks
        12. Delete both frame states from the repo
        13. Assert that the video state is now also AnnotationState.NONE for both tasks
        """
        project = fxt_detection_segmentation_chain_project_persisted
        task_ids = [task.id_ for task in project.get_trainable_task_nodes()]
        dataset_storage = project.get_training_dataset_storage()

        annotation_state_repo = AnnotationSceneStateRepo(dataset_storage.identifier)

        frame_1_identifier = VideoFrameIdentifier(video_id=ID(fxt_mongo_id(0)), frame_index=0)
        frame_2_identifier = VideoFrameIdentifier(video_id=ID(fxt_mongo_id(0)), frame_index=30)
        with (
            patch.object(
                IdentifierFactory,
                "generate_frame_identifiers_for_video",
                return_value=[frame_1_identifier, frame_2_identifier],
            ),
            patch.object(
                VideoRepo,
                "get_by_id",
                return_value=fxt_video_entity,
            ),
        ):
            video_identifier = VideoIdentifier(video_id=ID(fxt_mongo_id(0)))

            # Test that the method works correctly  with 2 AnnotationState.ANNOTATED states
            frame_1_state = AnnotationSceneState(
                media_identifier=frame_1_identifier,
                annotation_scene_id=fxt_mongo_id(1),
                annotation_state_per_task={
                    task_ids[0]: AnnotationState.ANNOTATED,
                    task_ids[1]: AnnotationState.ANNOTATED,
                },
                unannotated_rois={fxt_mongo_id(2): []},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
            frame_2_state = AnnotationSceneState(
                media_identifier=frame_2_identifier,
                annotation_scene_id=fxt_mongo_id(1),
                annotation_state_per_task={
                    task_ids[0]: AnnotationState.ANNOTATED,
                    task_ids[1]: AnnotationState.ANNOTATED,
                },
                unannotated_rois={fxt_mongo_id(2): [fxt_mongo_id(3)]},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
            annotation_state_repo.save(frame_1_state)
            annotation_state_repo.save(frame_2_state)

            frame_states_from_repo = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
                media_identifiers=[frame_1_identifier, frame_2_identifier],
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )
            assert frame_states_from_repo == {
                frame_1_identifier: {
                    task_ids[0]: AnnotationState.ANNOTATED,
                    task_ids[1]: AnnotationState.ANNOTATED,
                },
                frame_2_identifier: {
                    task_ids[0]: AnnotationState.ANNOTATED,
                    task_ids[1]: AnnotationState.ANNOTATED,
                },
            }
            video_state_from_repo = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
                media_identifiers=[video_identifier],
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )
            assert video_state_from_repo == {
                video_identifier: {
                    task_ids[0]: None,
                    task_ids[1]: None,
                }
            }

            # Test that the method works correctly with one ANNOTATED and one PARTIALLY_ANNOTATED state
            frame_1_state.state_per_task = {
                task_ids[0]: AnnotationState.ANNOTATED,
                task_ids[1]: AnnotationState.PARTIALLY_ANNOTATED,
            }
            annotation_state_repo.save(frame_1_state)
            video_state_from_repo = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
                media_identifiers=[video_identifier],
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )
            assert video_state_from_repo == {
                video_identifier: {
                    task_ids[0]: None,
                    task_ids[1]: None,
                }
            }
            # Test that the method works correctly with one ANNOTATED and one TO_REVISIT state
            frame_1_state = AnnotationSceneState(
                media_identifier=frame_1_identifier,
                annotation_scene_id=fxt_mongo_id(1),
                annotation_state_per_task={
                    task_ids[0]: AnnotationState.ANNOTATED,
                    task_ids[1]: AnnotationState.ANNOTATED,
                },
                labels_to_revisit_full_scene=[fxt_mongo_id(5)],
                unannotated_rois={fxt_mongo_id(2): []},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
            annotation_state_repo.save(frame_1_state)
            video_state_from_repo = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
                media_identifiers=[video_identifier],
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )
            assert video_state_from_repo == {
                video_identifier: {
                    task_ids[0]: None,
                    task_ids[1]: None,
                }
            }

            # Test that the method works correctly with two AnnotationState.NONE states
            frame_1_state = AnnotationSceneState(
                media_identifier=frame_1_identifier,
                annotation_scene_id=fxt_mongo_id(1),
                annotation_state_per_task={
                    task_ids[0]: AnnotationState.NONE,
                    task_ids[1]: AnnotationState.NONE,
                },
                unannotated_rois={fxt_mongo_id(2): []},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
            frame_2_state.state_per_task = {
                task_ids[0]: AnnotationState.NONE,
                task_ids[1]: AnnotationState.NONE,
            }
            annotation_state_repo.save(frame_1_state)
            annotation_state_repo.save(frame_2_state)
            video_state_from_repo = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
                media_identifiers=[video_identifier],
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )
            assert video_state_from_repo == {
                video_identifier: {
                    task_ids[0]: None,
                    task_ids[1]: None,
                }
            }

            # Test that the method works correctly when there are no states in the repo
            annotation_state_repo.delete_all_by_media_id(video_identifier.media_id)
            frame_states_from_repo = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
                media_identifiers=[frame_1_identifier, frame_2_identifier],
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )
            assert frame_states_from_repo == {
                frame_1_identifier: {
                    task_ids[0]: AnnotationState.NONE,
                    task_ids[1]: AnnotationState.NONE,
                },
                frame_2_identifier: {
                    task_ids[0]: AnnotationState.NONE,
                    task_ids[1]: AnnotationState.NONE,
                },
            }
            video_state_from_repo = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
                media_identifiers=[video_identifier],
                dataset_storage_identifier=dataset_storage.identifier,
                project=project,
            )
            assert video_state_from_repo == {
                video_identifier: {
                    task_ids[0]: None,
                    task_ids[1]: None,
                }
            }

    def test_get_unannotated_media_identifiers_in_dataset_storage(
        self, fxt_mongo_id, fxt_detection_segmentation_chain_project_persisted
    ) -> None:
        """
        <b>Description:</b>
        Check that the query for per-task state of a list of media identifiers works for video frames as well as videos.

        <b>Input data:</b>
        An detection->classification chain project

        <b>Expected results:</b>
        The AnnotationSceneStateRepo gets the correct annotation states on the media level for videos and frames.

        <b>Steps</b>
        1. Create an empty detection->classification chain project and initiate AnnotationSceneStateRepo
        2. Create two VideoFrameIdentifier entities and save fully annotated states to the repo for both frames
        3. Patch the video repo to return the two identifiers when identifiers are queried
        4. Query the unannotated states in the repo and assert none are found
        5. Set the state to NONE for the second task for one of the frames and assert the method still finds no
            unannotated identifiers.
        6. Set the state to NONE for both tasks for one of the frames and assert the method now finds this frame
        7. Set the state to NONE for both tasks for the other frame. ASsert that the method still finds one frame, if
        the parameter max_unseen_media is used.
        """
        project = fxt_detection_segmentation_chain_project_persisted
        task_ids = [task.id_ for task in project.get_trainable_task_nodes()]
        dataset_storage = project.get_training_dataset_storage()
        ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage.identifier)

        frame_1_identifier = VideoFrameIdentifier(video_id=ID(fxt_mongo_id(0)), frame_index=0)
        frame_2_identifier = VideoFrameIdentifier(video_id=ID(fxt_mongo_id(0)), frame_index=30)

        frame_1_state = AnnotationSceneState(
            media_identifier=frame_1_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            annotation_state_per_task={
                task_ids[0]: AnnotationState.ANNOTATED,
                task_ids[1]: AnnotationState.ANNOTATED,
            },
            unannotated_rois={fxt_mongo_id(2): []},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        frame_2_state = AnnotationSceneState(
            media_identifier=frame_2_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            annotation_state_per_task={
                task_ids[0]: AnnotationState.ANNOTATED,
                task_ids[1]: AnnotationState.ANNOTATED,
            },
            unannotated_rois={fxt_mongo_id(2): [fxt_mongo_id(3)]},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        ann_scene_state_repo.save(frame_1_state)
        ann_scene_state_repo.save(frame_2_state)
        with patch.object(
            VideoRepo,
            "get_frame_identifiers",
            return_value=[frame_1_identifier, frame_2_identifier],
        ):
            unannotated_identifiers = list(
                AnnotationSceneStateHelper.get_unannotated_media_identifiers_in_dataset_storage(
                    dataset_storage_identifier=dataset_storage.identifier,
                    project=fxt_detection_segmentation_chain_project_persisted,
                )
            )
            assert unannotated_identifiers == []

            frame_1_state.state_per_task = {
                task_ids[0]: AnnotationState.ANNOTATED,
                task_ids[1]: AnnotationState.NONE,
            }
            ann_scene_state_repo.save(frame_1_state)
            unannotated_identifiers = list(
                AnnotationSceneStateHelper.get_unannotated_media_identifiers_in_dataset_storage(
                    dataset_storage_identifier=dataset_storage.identifier,
                    project=fxt_detection_segmentation_chain_project_persisted,
                )
            )
            assert unannotated_identifiers == []

            frame_1_state.state_per_task = {
                task_ids[0]: AnnotationState.NONE,
                task_ids[1]: AnnotationState.NONE,
            }
            ann_scene_state_repo.save(frame_1_state)
            unannotated_identifiers = list(
                AnnotationSceneStateHelper.get_unannotated_media_identifiers_in_dataset_storage(
                    dataset_storage_identifier=dataset_storage.identifier,
                    project=fxt_detection_segmentation_chain_project_persisted,
                )
            )
            assert unannotated_identifiers == [frame_1_identifier]

            frame_2_state.state_per_task = {
                task_ids[0]: AnnotationState.NONE,
                task_ids[1]: AnnotationState.NONE,
            }
            ann_scene_state_repo.save(frame_2_state)
            unannotated_identifiers = list(
                AnnotationSceneStateHelper.get_unannotated_media_identifiers_in_dataset_storage(
                    dataset_storage_identifier=dataset_storage.identifier,
                    project=fxt_detection_segmentation_chain_project_persisted,
                    max_unseen_media=1,
                )
            )
            assert len(unannotated_identifiers) == 1

    def test_get_state_for_scene(
        self,
        fxt_annotation_scene,
        fxt_annotation_scene_state,
        fxt_dataset_storage,
        fxt_empty_project,
    ) -> None:
        """
        Unit test for AnnotationSceneHelper.get_annotation_state_for_scene
        """
        # Arrange
        with patch.object(
            AnnotationSceneStateRepo,
            "get_latest_for_annotation_scene",
            return_value=fxt_annotation_scene_state,
        ):
            # Act
            result = AnnotationSceneStateHelper.get_annotation_state_for_scene(
                annotation_scene=fxt_annotation_scene,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                project=fxt_empty_project,
            )

        # Assert
        assert result == fxt_annotation_scene_state

    def test_get_state_for_scene_not_found(
        self,
        fxt_annotation_scene,
        fxt_dataset_storage,
        fxt_empty_project,
    ) -> None:
        """
        Unit test for AnnotationSceneHelper.get_annotation_state_for_scene. Checks that if the scene is not in the repo,
        it's computed on the spot.
        """
        # Arrange
        with patch.object(
            AnnotationSceneStateRepo,
            "get_latest_for_annotation_scene",
            return_value=NullAnnotationSceneState(),
        ):
            # Act
            result = AnnotationSceneStateHelper.get_annotation_state_for_scene(
                annotation_scene=fxt_annotation_scene,
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                project=fxt_empty_project,
            )
            expected_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                fxt_annotation_scene, project=fxt_empty_project
            )
            expected_state.id_ = result.id_

        assert result == expected_state

    def test_get_states_for_scenes(
        self,
        fxt_annotation_scene,
        fxt_annotation_scene_state,
        fxt_dataset_storage,
        fxt_empty_project,
    ) -> None:
        """
        Unit test for AnnotationSceneHelper.get_annotation_states_for_scenes
        """
        # Arrange
        with patch.object(
            AnnotationSceneStateRepo,
            "get_latest_for_annotation_scenes",
            return_value={fxt_annotation_scene.id_: fxt_annotation_scene_state},
        ):
            # Act
            result = AnnotationSceneStateHelper.get_annotation_states_for_scenes(
                annotation_scenes=[fxt_annotation_scene],
                dataset_storage=fxt_dataset_storage,
                project=fxt_empty_project,
            )

        # Assert
        assert result == {fxt_annotation_scene.id_: fxt_annotation_scene_state}

    def test_get_states_for_scenes_not_found(
        self,
        fxt_annotation_scene,
        fxt_dataset_storage,
        fxt_empty_project,
    ) -> None:
        """
        Unit test for AnnotationSceneHelper.get_annotation_states_for_scenes. Checks that if a scene is not in the repo,
        it's computed on the spot.
        """
        # Arrange
        with patch.object(
            AnnotationSceneStateRepo,
            "get_latest_for_annotation_scenes",
            return_value={},
        ):
            # Act
            result = AnnotationSceneStateHelper.get_annotation_states_for_scenes(
                annotation_scenes=[fxt_annotation_scene],
                dataset_storage=fxt_dataset_storage,
                project=fxt_empty_project,
            )
            expected_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                fxt_annotation_scene, project=fxt_empty_project
            )
            expected_state.id_ = result[fxt_annotation_scene.id_].id_

        # Assert
        assert result == {fxt_annotation_scene.id_: expected_state}
