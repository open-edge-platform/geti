# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements project fixtures
"""

import pytest
from _pytest.fixtures import FixtureRequest
from geti_types import ID
from iai_core.algorithms import ModelTemplateList
from iai_core.entities.color import Color
from iai_core.entities.keypoint_structure import KeypointEdge, KeypointPosition, KeypointStructure
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema, LabelSchemaView
from iai_core.entities.model_template import HyperParameterData, InstantiationType, ModelTemplate, TaskFamily, TaskType
from iai_core.entities.project import Project
from iai_core.entities.shapes import Rectangle
from iai_core.entities.task_graph import TaskEdge, TaskGraph
from iai_core.entities.task_node import TaskNode, TaskProperties
from iai_core.repos import LabelRepo, LabelSchemaRepo, TaskNodeRepo
from iai_core.utils.project_factory import ProjectFactory

from tests.test_helpers import (
    generate_ellipse_shape,
    generate_images_and_annotation_scenes,
    generate_keypoint_shape,
    generate_polygon_shape,
    generate_random_video,
    generate_rectangle_shape,
    generated_rotated_rectangle_shape,
    get_project_labels,
    register_model_template,
)

supported_task_types = [
    TaskType.DETECTION,
    TaskType.ROTATED_DETECTION,
    TaskType.SEGMENTATION,
    TaskType.CLASSIFICATION,
    TaskType.INSTANCE_SEGMENTATION,
    TaskType.ANOMALY_CLASSIFICATION,
    TaskType.ANOMALY_DETECTION,
    TaskType.ANOMALY_SEGMENTATION,
    TaskType.KEYPOINT_DETECTION,
]
for task_type in supported_task_types:
    mock_name = f"mock_{task_type.name.lower()}"
    model_template = ModelTemplate(
        model_template_id=mock_name,
        model_template_path="",
        name=mock_name,
        task_type=task_type,
        task_family=TaskFamily.VISION,
        instantiation=InstantiationType.NONE,
        hyper_parameters=HyperParameterData(base_path=""),
        capabilities=["compute_representations"],
        is_default_for_task=True,
    )
    ModelTemplateList().register_model_template(model_template)


@pytest.fixture
def fxt_annotated_classification_project(request):
    name = "_test_classification_project"
    model_template_id = "classification"
    register_model_template(
        request,
        type(None),
        model_template_id,
        trainable=True,
        task_type="CLASSIFICATION",
    )
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ],
        model_template_id=model_template_id,
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        labels=labels,
        shape_generator=Rectangle.generate_full_box,
    )

    return project


@pytest.fixture
def fxt_annotated_hierarchical_classification_project(request):
    name = "_test_hierarchical_classification_project"
    model_template_id = "classification"
    register_model_template(
        request,
        type(None),
        model_template_id,
        trainable=True,
        task_type="CLASSIFICATION",
    )
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "right", "color": "#5B69FF"},
            {"name": "square", "color": "#80E9AF"},
            {"name": "equilateral", "color": "#9D3B1A"},
            {"name": "rectangle", "color": "#009BDD9A"},
            {"name": "triangle", "color": "#00286DDE"},
            {"name": "non_square", "color": "#708541"},
        ],
        model_template_id=model_template_id,
        label_groups=[
            {
                "name": "shape",
                "labels": ["rectangle", "triangle"],
                "group_type": "exclusive",
            },
            {
                "name": "rectangle default",
                "labels": ["non_square", "square"],
                "group_type": "exclusive",
            },
            {
                "name": "triangle default",
                "labels": ["equilateral", "right"],
                "group_type": "exclusive",
            },
        ],
        labelname_to_parent={
            "square": "rectangle",
            "non_square": "rectangle",
            "equilateral": "triangle",
            "right": "triangle",
        },
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=15,
        num_unannotated_images=4,
        labels=labels,
        shape_generator=Rectangle.generate_full_box,
    )

    return project


@pytest.fixture
def fxt_annotated_hierarchical_classification_with_multi_label_project(
    request,
):
    model_template_id = "classification"
    register_model_template(
        request,
        type(None),
        model_template_id,
        trainable=True,
        task_type="CLASSIFICATION",
    )
    name = "_test_hierarchical_classification_with_multi_label_project"
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "rectangle", "color": "#009BDD9A"},
            {"name": "triangle", "color": "#00286DDE"},
            {"name": "square", "color": "#80E9AF"},
            {"name": "non_square", "color": "#708541"},
            {"name": "red rectangle", "color": "#5B69FF"},
            {"name": "blue rectangle", "color": "#9D3B1A"},
        ],
        model_template_id=model_template_id,
        label_groups=[
            {
                "name": "rectangle",
                "labels": ["rectangle"],
                "group_type": "exclusive",
            },
            {
                "name": "square",
                "labels": ["square"],
                "group_type": "exclusive",
            },
            {
                "name": "non_square",
                "labels": ["non_square"],
                "group_type": "exclusive",
            },
            {
                "name": "red rectangle",
                "labels": ["red rectangle"],
                "group_type": "exclusive",
            },
            {
                "name": "blue rectangle",
                "labels": ["blue rectangle"],
                "group_type": "exclusive",
            },
        ],
        labelname_to_parent={
            "square": "rectangle",
            "non_square": "rectangle",
            "red rectangle": "rectangle",
            "blue rectangle": "rectangle",
        },
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=15,
        num_unannotated_images=4,
        labels=labels,
        shape_generator=Rectangle.generate_full_box,
    )

    return project


@pytest.fixture
def fxt_annotated_detection_project(request):
    name = "_test_det_project"
    model_template_id = "detection"
    register_model_template(request, type(None), model_template_id, trainable=True, task_type="DETECTION")
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ],
        model_template_id=model_template_id,
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        labels=labels,
        shape_generator=generate_rectangle_shape,
    )

    generate_random_video(project=project, video_name="Annotated Video", generate_annotations=True)

    generate_random_video(project=project, video_name="Unannotated Video", generate_annotations=False)

    return project


@pytest.fixture
def fxt_annotated_rotated_detection_project(request):
    model_template_id = "rotated_detection"
    register_model_template(
        request,
        type(None),
        model_template_id,
        trainable=True,
        task_type="ROTATED_DETECTION",
    )
    name = "_test_rotated_det_project"
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ],
        model_template_id=model_template_id,
    )
    labels = get_project_labels(project)
    empty_labels = [label for label in get_project_labels(project, include_empty=True) if label.is_empty]
    if len(empty_labels) == 0:
        empty_labels = None

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        num_empty_annotated_images=4,
        labels=labels,
        empty_labels=empty_labels,
        shape_generator=generated_rotated_rectangle_shape,
    )

    return project


def get_annotated_segmentation_project(task_type: TaskType, request: FixtureRequest):
    model_template_id = task_type.name.lower()
    register_model_template(request, type(None), model_template_id, trainable=True, task_type=task_type.name)
    name = f"_test_{model_template_id}_project"
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ],
        model_template_id=model_template_id,
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        labels=labels,
        shape_generators={
            "rectangle": generate_rectangle_shape,
            "ellipse": generate_ellipse_shape,
            "triangle": generate_polygon_shape,
        },
    )

    return project


@pytest.fixture
def fxt_annotated_segmentation_project(request):
    return get_annotated_segmentation_project(TaskType.SEGMENTATION, request)


@pytest.fixture
def fxt_annotated_instance_segmentation_project(request):
    return get_annotated_segmentation_project(TaskType.INSTANCE_SEGMENTATION, request)


@pytest.fixture
def fxt_annotated_anomaly_cls_project(request):
    model_template_id = "anomaly_classification"
    register_model_template(
        request,
        type(None),
        model_template_id,
        trainable=True,
        task_type="ANOMALY_CLASSIFICATION",
    )
    name = "_test_anom_cls_project"
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "normal", "color": "#00ff00ff"},
            {"name": "anomalous", "color": "#0000ffff"},
        ],
        model_template_id=model_template_id,
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        labels=labels,
        shape_generator=Rectangle.generate_full_box,
    )

    return project


@pytest.fixture
def fxt_annotated_anomaly_cls_project_with_video(fxt_annotated_anomaly_cls_project):
    project = fxt_annotated_anomaly_cls_project

    generate_random_video(project=project)

    return project


@pytest.fixture
def fxt_annotated_anomaly_seg_project(request):
    model_template_id = "anomaly_segmentation"
    register_model_template(
        request,
        type(None),
        model_template_id,
        trainable=True,
        task_type="ANOMALY_SEGMENTATION",
    )
    name = "_test_anom_seg_project"
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "normal", "color": "#00ff00ff"},
            {"name": "anomalous", "color": "#0000ffff"},
        ],
        model_template_id=model_template_id,
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        labels=labels,
        shape_generators={
            "normal": Rectangle.generate_full_box,
            "anomalous": generate_polygon_shape,
        },
    )

    return project


@pytest.fixture
def fxt_annotated_anomaly_det_project(request):
    model_template_id = "anomaly_detection"
    register_model_template(
        request,
        type(None),
        model_template_id,
        trainable=True,
        task_type="ANOMALY_DETECTION",
    )
    name = "_test_anom_det_project"
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "normal", "color": "#00ff00ff"},
            {"name": "anomalous", "color": "#0000ffff"},
        ],
        model_template_id=model_template_id,
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        labels=labels,
        shape_generators={
            "normal": Rectangle.generate_full_box,
            "anomalous": generate_rectangle_shape,
        },
    )

    return project


def _create_chained_project(request: FixtureRequest, is_det_cls: bool = True) -> Project:
    # prepare model templates
    dataset_template = ModelTemplateList().get_by_id("dataset")
    detection_template = register_model_template(
        request, type(None), "detection", trainable=True, task_type="DETECTION"
    )
    crop_template = register_model_template(request, type(None), "crop", trainable=False, task_type="CROP")
    model_templates = [dataset_template, detection_template, crop_template]

    if is_det_cls:
        model_templates.append(
            register_model_template(
                request,
                type(None),
                "classification",
                trainable=True,
                task_type="CLASSIFICATION",
            )
        )
        name = "chained_det_cls_project"
        seconed_domain = Domain.CLASSIFICATION
        shape_generator = generate_rectangle_shape
        shape_generators = None
    else:  # det_seg
        model_templates.append(
            register_model_template(
                request,
                type(None),
                "segmentation",
                trainable=True,
                task_type="SEGMENTATION",
            )
        )
        name = "chained_det_seg_project"
        seconed_domain = Domain.SEGMENTATION
        shape_generator = None
        shape_generators = {
            "object": generate_rectangle_shape,
            "rectangle": generate_rectangle_shape,
            "circle": generate_ellipse_shape,
            "triangle": generate_polygon_shape,
        }

    # prepare task graph
    task_nodes = []
    for model_template in model_templates:
        node = TaskNode(
            title=f"{model_template.model_template_id} task node",
            project_id=ID(),
            task_properties=TaskProperties.from_model_template(model_template),
            id_=TaskNodeRepo.generate_id(),
        )
        task_nodes.append(node)
    task_graph = TaskGraph()
    for i in range(len(task_nodes) - 1):
        task_graph.add_task_edge(TaskEdge(from_task=task_nodes[i], to_task=task_nodes[i + 1]))

    # Create project
    project = ProjectFactory.create_project_with_task_graph(
        name=name,
        creator_id="",
        description=name,
        task_graph=task_graph,
        model_templates=model_templates,
    )

    # Create labels
    object_label = Label(
        name="object",
        domain=Domain.DETECTION,
        color=Color(255, 255, 0),
        id_=LabelRepo.generate_id(),
    )
    triangle_label = Label(
        name="triangle",
        domain=seconed_domain,
        color=Color(255, 0, 0),
        id_=LabelRepo.generate_id(),
    )
    rectangle_label = Label(
        name="rectangle",
        domain=seconed_domain,
        color=Color(0, 255, 0),
        id_=LabelRepo.generate_id(),
    )
    circle_label = Label(
        name="circle",
        domain=seconed_domain,
        color=Color(0, 0, 255),
        id_=LabelRepo.generate_id(),
    )
    detection_labels = [object_label]
    second_task_labels = [triangle_label, rectangle_label, circle_label]

    # Create label schema and its views
    det_group = LabelGroup("Detection", detection_labels, LabelGroupType.EXCLUSIVE)
    cls_group = LabelGroup(seconed_domain.name, second_task_labels, LabelGroupType.EXCLUSIVE)
    label_schema = LabelSchema(
        id_=LabelSchemaRepo.generate_id(),
        label_groups=[det_group, cls_group],
        project_id=project.id_,
    )
    for label in second_task_labels:
        label_schema.add_child(object_label, label)
    detection_label_schema = LabelSchemaView.from_parent(
        parent_schema=label_schema,
        labels=detection_labels,
        task_node_id=task_nodes[1].id_,  # detection node
        id_=LabelSchemaRepo.generate_id(),
    )
    second_task_label_schema = LabelSchemaView.from_parent(
        parent_schema=label_schema,
        labels=second_task_labels,
        task_node_id=task_nodes[3].id_,  # classification or segmentation.
        id_=LabelSchemaRepo.generate_id(),
    )
    label_schema_repo = LabelSchemaRepo(project.identifier)
    for schema in (label_schema, detection_label_schema, second_task_label_schema):
        label_schema_repo.save(schema)
        request.addfinalizer(lambda: label_schema_repo.delete_by_id(schema.id_))

    labels = get_project_labels(project)
    label_map = {label.name: label for label in labels}
    label_groups = [
        [label_map["object"], label_map["triangle"]],
        [label_map["object"], label_map["rectangle"]],
        [label_map["object"], label_map["circle"]],
    ]

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        label_groups=label_groups,
        shape_generator=shape_generator,
        shape_generators=shape_generators,
    )

    return project


@pytest.fixture
def fxt_annotated_chained_det_cls_project(request):
    return _create_chained_project(request)


@pytest.fixture
def fxt_annotated_chained_det_seg_project(request):
    return _create_chained_project(request, is_det_cls=False)


@pytest.fixture
def fxt_annotated_multi_label_project(request):
    model_template_id = "classification"
    register_model_template(
        request,
        type(None),
        model_template_id,
        trainable=True,
        task_type="CLASSIFICATION",
    )
    name = "_test_multi_label_project"
    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "cat", "color": "#00ff00ff"},
            {"name": "dog", "color": "#0000ffff"},
            {"name": "male", "color": "#ff0000ff"},
            {"name": "female", "color": "#ff00ffff"},
        ],
        model_template_id="classification",
        label_groups=[
            {
                "name": "group-cat",
                "labels": ["cat"],
                "group_type": "exclusive",
            },
            {
                "name": "group-dog",
                "labels": ["dog"],
                "group_type": "exclusive",
            },
            {
                "name": "group-male",
                "labels": ["male"],
                "group_type": "exclusive",
            },
            {
                "name": "group-female",
                "labels": ["female"],
                "group_type": "exclusive",
            },
        ],
        is_multi_label_classification=True,
    )
    labels = get_project_labels(project)

    label_map = {label.name: label for label in labels}
    label_groups = [
        [label_map["cat"], label_map["male"]],
        [label_map["cat"], label_map["female"]],
        [label_map["dog"], label_map["male"]],
        [label_map["dog"], label_map["female"]],
    ]

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        label_groups=label_groups,
        shape_generator=Rectangle.generate_full_box,
    )

    return project


@pytest.fixture
def fxt_label_schema_hierarchical() -> LabelSchema:
    return LabelSchema(
        id_=LabelSchemaRepo.generate_id(),
        label_groups=[
            LabelGroup(
                name="rectangle default",
                labels=[
                    Label(
                        id_=LabelRepo.generate_id(),
                        name="square",
                        domain=Domain.CLASSIFICATION,
                    ),
                    Label(
                        id_=LabelRepo.generate_id(),
                        name="non_square",
                        domain=Domain.CLASSIFICATION,
                    ),
                ],
            ),
            LabelGroup(
                name="triangle default",
                labels=[
                    Label(
                        id_=LabelRepo.generate_id(),
                        name="right",
                        domain=Domain.CLASSIFICATION,
                    ),
                    Label(
                        id_=LabelRepo.generate_id(),
                        name="equilateral",
                        domain=Domain.CLASSIFICATION,
                    ),
                ],
            ),
            LabelGroup(name="labels", labels=[]),
        ],
    )


@pytest.fixture
def fxt_label_schema_classification() -> LabelSchema:
    return LabelSchema(
        id_=LabelSchemaRepo.generate_id(),
        label_groups=[
            LabelGroup(
                name="labels",
                labels=[
                    Label(
                        id_=LabelRepo.generate_id(),
                        name="rectangle",
                        domain=Domain.CLASSIFICATION,
                    ),
                    Label(
                        id_=LabelRepo.generate_id(),
                        name="ellipse",
                        domain=Domain.CLASSIFICATION,
                    ),
                    Label(
                        id_=LabelRepo.generate_id(),
                        name="triangle",
                        domain=Domain.CLASSIFICATION,
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def fxt_keypoint_detection_project(request) -> Project:
    name = "_test_keypoint_project"
    model_template_id = "keypoint_detection"
    register_model_template(request, type(None), model_template_id, trainable=True, task_type="KEYPOINT_DETECTION")

    edges = []
    positions = []
    edges.append(KeypointEdge(node_1=ID("rectangle"), node_2=ID("ellipse")))
    edges.append(KeypointEdge(node_1=ID("ellipse"), node_2=ID("triangle")))
    positions.append(KeypointPosition(node=ID("rectangle"), x=0.3, y=0.3))
    positions.append(KeypointPosition(node=ID("ellipse"), x=0.4, y=0.4))
    positions.append(KeypointPosition(node=ID("triangle"), x=0.5, y=0.5))
    keypoint_structure = KeypointStructure(edges=edges, positions=positions)

    project = ProjectFactory.create_project_single_task(
        name=name,
        description=name,
        creator_id="",
        labels=[
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ],
        model_template_id=model_template_id,
        keypoint_structure=keypoint_structure,
    )
    labels = get_project_labels(project)

    generate_images_and_annotation_scenes(
        project=project,
        num_annotated_images=10,
        num_unannotated_images=2,
        labels=labels,
        shape_generator=generate_keypoint_shape,
    )

    generate_random_video(project=project, video_name="Annotated Video", generate_annotations=True)
    generate_random_video(project=project, video_name="Unannotated Video", generate_annotations=False)

    return project
