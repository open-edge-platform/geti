# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
import os
import tempfile
import unittest
from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any

import cv2
import numpy as np
from pytest import FixtureRequest
from testfixtures import compare

from communication.constants import MAX_UNANNOTATED_DATASET_SIZE

import iai_core.configuration.helper as otx_config_helper
from geti_kafka_tools import publish_event
from geti_types import (
    CTX_SESSION_VAR,
    ID,
    DatasetStorageIdentifier,
    ImageIdentifier,
    ProjectIdentifier,
    VideoFrameIdentifier,
)
from iai_core.adapters.binary_interpreters import NumpyBinaryInterpreter
from iai_core.algorithms import ModelTemplateList
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.configuration.elements.hyper_parameters import HyperParameters
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.dataset_entities import TaskDataset
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.image import Image
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.model_template import ModelTemplate
from iai_core.entities.persistent_entity import PersistentEntity
from iai_core.entities.project import Project
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Ellipse, Point, Polygon, Rectangle
from iai_core.entities.task_graph import TaskEdge, TaskGraph
from iai_core.entities.task_node import TaskNode
from iai_core.entities.video import Video
from iai_core.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    ConfigurableParametersRepo,
    DatasetRepo,
    LabelSchemaRepo,
    ProjectRepo,
    VideoRepo,
)
from iai_core.repos.mappers.mongodb_mapper_interface import (
    IMapperBackward,
    IMapperDatasetStorageBackward,
    IMapperDatasetStorageForward,
    IMapperDatasetStorageIdentifierBackward,
    IMapperForward,
    IMapperModelStorageBackward,
    IMapperModelStorageForward,
    IMapperParametricBackward,
    IMapperParametricForward,
    IMapperProjectIdentifierBackward,
    MappableEntityType,
    MapperClassT,
)
from iai_core.repos.storage.binary_repos import ImageBinaryRepo
from iai_core.services.model_service import ModelService
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.media_factory import Media2DFactory
from iai_core.utils.project_factory import ProjectFactory

logger = logging.getLogger(__name__)


def auto_wire_task_chain(task_nodes: list[TaskNode]) -> TaskGraph:
    """
    Make a TaskGraph with a linear task chain, based on order of task_nodes.
    It'll automatically find the ports and create the edges, based on the given data_type.

    :param task_nodes: List of TaskNode to chain
    :return: TaskGraph
    """
    task_graph = TaskGraph()
    for i in range(max(len(task_nodes) - 1, 0)):
        from_task = task_nodes[i]
        to_task = task_nodes[i + 1]

        task_edge = TaskEdge(from_task=from_task, to_task=to_task)
        task_graph.add_task_edge(task_edge)

    return task_graph


def get_unannotated_dataset(
    project: Project,
    dataset_storage: DatasetStorage,
    max_dataset_size: int | None = None,
) -> Dataset:
    """
    Retrieve a dataset made out of the media without annotations.
    :param project: Project for which to get the unannotated dataset
    :param dataset_storage: DatasetStorage containing the dataset items, annotations and media.
    :param max_dataset_size: Optional, max number of items in the dataset.
        If None, it caps at 10k elements.
    :return: dataset of unannotated items
    """

    if max_dataset_size is None:
        max_dataset_size = MAX_UNANNOTATED_DATASET_SIZE

    num_unannotated_ids_to_fetch = max_dataset_size

    unannotated_identifiers = tuple(
        AnnotationSceneStateHelper.get_unannotated_media_identifiers_in_dataset_storage(
            dataset_storage_identifier=dataset_storage.identifier,
            project=project,
            max_unseen_media=num_unannotated_ids_to_fetch,
        )
    )

    dataset = Dataset(id=DatasetRepo.generate_id())
    for identifier in unannotated_identifiers:
        media = Media2DFactory().get_media_for_identifier(
            identifier, dataset_storage_identifier=dataset_storage.identifier
        )
        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.INTERMEDIATE,
            media_identifier=identifier,
            media_height=media.height,
            media_width=media.width,
            id_=AnnotationSceneRepo.generate_id(),
        )
        item = DatasetItem(
            media=media,
            annotation_scene=annotation_scene,
            id_=DatasetRepo.generate_id(),
        )
        dataset.append(item)
    return dataset


def construct_and_save_train_dataset_for_task(
    task_dataset_entity: TaskDataset,
    project_id: ID,
    task_node: TaskNode,
    dataset_storage: DatasetStorage,
) -> Dataset:
    """
    This method does the following:
    1. Fetches the current dataset from the task dataset entity
    2. Calls the subset manager to set the unassigned subsets in the dataset
    3. Save the new subsets to the repo by calling update_subsets and publish that the subsets were updated
    4. Makes a copy of the dataset and passes it to the training operator

    :param task_dataset_entity: TaskDataset that holds the current dataset for the task
    :param project_id: ID of the project
    :param task_node: Task node for which the dataset is fetched
    :param dataset_storage: DatasetStorage containing the dataset items
    :return: A copy of the current dataset, split into subsets.
    """
    workspace_id = CTX_SESSION_VAR.get().workspace_id
    project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
    task_label_schema = LabelSchemaRepo(project_identifier).get_latest_view_by_task(task_node_id=task_node.id_)

    dataset = task_dataset_entity.get_dataset(dataset_storage=dataset_storage)

    task_dataset_entity.save_subsets(dataset=dataset, dataset_storage_identifier=dataset_storage.identifier)
    assigned_items_list_string = [str(assigned_item.id_) for assigned_item in dataset]
    publish_event(
        topic="dataset_updated",
        body={
            "workspace_id": str(workspace_id),
            "project_id": str(project_id),
            "task_node_id": str(task_node.id_),
            "dataset_id": str(task_dataset_entity.dataset_id),
            "new_dataset_items": [],
            "deleted_dataset_items": [],
            "assigned_dataset_items": assigned_items_list_string,
        },
        key=str(task_node.id_).encode(),
    )
    for item in dataset:
        item.id_ = DatasetRepo.generate_id()
    new_training_dataset = Dataset(
        items=list(dataset),
        purpose=DatasetPurpose.TRAINING,
        label_schema_id=task_label_schema.id_,
        id=DatasetRepo.generate_id(),
    )
    DatasetRepo(dataset_storage.identifier).save_deep(new_training_dataset)
    return new_training_dataset


def generate_random_annotated_image(
    image_width: int,
    image_height: int,
    labels: Sequence[Label],
    min_size=50,
    max_size=250,
    max_shapes: int = 10,
) -> tuple[np.ndarray, list[Annotation]]:
    """
    Generate a random image with the corresponding annotation entities.

    :param max_shapes: Maximum amount of shapes in the image
    :param image_height: Height of the image
    :param image_width: Width of the image
    :param labels: Task Labels that should be applied to the respective shape
    :param min_size: Minimum size of the shape(s)
    :param max_size: Maximum size of the shape(s)
    :return: uint8 array, list of shapes
    """
    assert min_size, max_size < image_width
    assert min_size, max_size < image_height
    img = (np.random.standard_normal([image_height, image_width, 3]) * 255).astype(np.uint8)
    label_map = {label.name: label for label in labels}
    rng = np.random.default_rng()
    num_shapes = rng.integers(low=1, high=max_shapes + 1)
    img_labels = rng.choice(list(label_map), num_shapes)

    annotations: list[Annotation] = []
    for label_name in img_labels:
        rx, ry = rng.integers(low=[1, 1], high=[image_width - min_size, image_height - min_size])
        rw, rh = rng.integers(
            low=[min_size, min_size],
            high=[min(max_size, image_width - rx), min(max_size, image_height - ry)],
        )
        y_min, y_max = float(ry / image_height), float((ry + rh) / image_height)
        x_min, x_max = float(rx / image_width), float((rx + rw) / image_width)

        label = next(label for label in labels if label_name == label.name)
        box_shape = Rectangle(x1=x_min, y1=y_min, x2=x_max, y2=y_max)
        scored_labels = [ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)]
        annotation = Annotation(box_shape, labels=scored_labels)

        if label_name == "ellipse":
            annotation = Annotation(
                Ellipse(
                    x1=box_shape.x1,
                    y1=box_shape.y1,
                    x2=box_shape.x2,
                    y2=box_shape.y2,
                ),
                labels=scored_labels,
            )
        elif label_name == "triangle":
            points = [
                Point(
                    x=(box_shape.x1 + box_shape.x2) / 2,
                    y=box_shape.y1,
                ),
                Point(x=box_shape.x1, y=box_shape.y2),
                Point(x=box_shape.x2, y=box_shape.y2),
            ]
            annotation = Annotation(
                Polygon(points=points),
                labels=scored_labels,
            )

        annotations.append(annotation)

    return img, annotations


def generate_random_annotated_video(
    project: Project, width: int = 480, height: int = 360, number_of_frames: int = 150
) -> tuple[Video, list[AnnotationScene]]:
    """
    generate a random video that is 150 frames at 30 fps. Video contains random shapes on white background
    NOTE: If you change the number of frames make sure to set overwrite to true if using the same video_path

    :param project: Project that the Video will added to
    :param width: Width of the video
    :param height: Height of the video
    :param number_of_frames: Amount of frames to generate
    :return: Tuple(Video entity, list of AnnotationScene entities)
    """

    annotations_per_frame = []  # List with list of annotations
    dataset_storage = project.get_training_dataset_storage()
    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=project.workspace_id,
        project_id=project.id_,
        dataset_storage_id=dataset_storage.id_,
    )
    video_repo = VideoRepo(dataset_storage_identifier)

    # Make a video path using video id and an extension
    video_id = video_repo.generate_id()
    video_path = os.path.join(tempfile.gettempdir(), f"{video_id}.mp4")

    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    fps = 30.0
    video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
    ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
    label_schema_repo = LabelSchemaRepo(project.identifier)
    project_label_schema = label_schema_repo.get_latest()
    # Generate frames
    for i in range(number_of_frames):
        img, annotations = generate_random_annotated_image(
            image_width=width,
            image_height=height,
            labels=project_label_schema.get_labels(include_empty=True),
            min_size=30,
        )
        annotations_per_frame.append(annotations)
        video_writer.write(img)
    video_writer.release()

    # Generate video
    filename = video_repo.binary_repo.save(data_source=video_path, dst_file_name=video_path)
    size = video_repo.binary_repo.get_object_size(video_path)

    _, extension = os.path.splitext(filename)
    try:
        video_extension = VideoExtensions[extension[1:].upper()]
    except KeyError:
        video_extension = VideoExtensions.MP4

    # Remove input binary after save
    if os.path.exists(video_path):
        os.remove(video_path)

    video = Video(
        name="Generated video",
        stride=1,
        id=video_id,
        uploader_id="",
        fps=fps,
        width=width,
        height=height,
        total_frames=number_of_frames,
        size=size,
        extension=video_extension,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )
    video_repo.save(video)

    # Generate annotations
    annotation_scenes = []
    for i, annotations in enumerate(annotations_per_frame):
        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=VideoFrameIdentifier(video_id=video.id_, frame_index=i),
            media_height=video.height,
            media_width=video.width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotations,
        )
        annotation_scenes.append(annotation_scene)
        ann_scene_repo.save(annotation_scene)
        media_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
            annotation_scene=annotation_scene,
            project=project,
        )
        ann_scene_state_repo.save(media_state)
    return video, annotation_scenes


def _repo_cleanup():
    """
    Clean up
    """

    def _cleanup() -> None:
        project_repo: ProjectRepo = ProjectRepo()
        for project in project_repo.get_all():
            DeletionHelpers.delete_project_by_id(project_id=project.id_)

    return _cleanup


def generate_random_annotated_project(
    test_case: unittest.TestCase | FixtureRequest | None,
    name: str,
    description: str,
    model_template_id: str | ModelTemplate,
    number_of_images: int = 25,
    number_of_videos: int = 1,
    image_width: int | Callable[[], int] = 512,
    image_height: int | Callable[[], int] = 384,
    max_shapes: int = 10,
    min_size_shape: int = 50,
    max_size_shape: int = 100,
    configurable_parameters: HyperParameters[ConfigurableParameters] | None = None,
    label_configs=None,
) -> tuple[Project, LabelSchema]:
    """
    Will create a randomly annotated project in the default workspace with images
    containing rectangles, circles and triangles in different colors

    :param test_case: Associated test case. The project will automatically be deleted at
           the end of the test case.
    :param name: Name of the project
    :param description: Description of the project
    :param model_template_id: Model template for project
        (either the model template ID or the model template itself)
    :param number_of_images: Number of images initially added to the project.
        Default value of 25 has been chosen to have a good chance to successfully train a model
    :param number_of_videos: Number of videos initially added to the project.
    :param image_width: Width of generated images
    :param image_height: Height of generated images
    :param max_shapes: Maximum number of shapes per image
    :param min_size_shape: The minimum size of the shape in pixels
    :param max_size_shape: the maximum size of the shape in pixels
    :param configurable_parameters: [Optionally] Set the configurable parameters for
        the newly created task in the project
    :param label_configs: List of label configuration which is a dictionary of label attributes
    :return: Generated project
    """

    if label_configs is None:
        label_configs = [
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ]
    from iai_core.repos import AnnotationSceneRepo, ImageRepo

    if isinstance(model_template_id, ModelTemplate):
        model_template_id = model_template_id.model_template_id

    if test_case is not None:
        if isinstance(test_case, FixtureRequest):
            test_case.addfinalizer(_repo_cleanup())
        else:
            test_case.addCleanup(_repo_cleanup())

    parameter_data = configurable_parameters.data if configurable_parameters is not None else None

    project_input = ProjectFactory.create_project_single_task(
        name=name,
        description=description,
        creator_id="",
        labels=label_configs,
        model_template_id=model_template_id,
        configurable_parameters=parameter_data,
    )
    dataset_storage = project_input.get_training_dataset_storage()
    dataset_storage_identifier = dataset_storage.identifier
    image_repo = ImageRepo(dataset_storage_identifier)
    image_binary_repo = ImageBinaryRepo(dataset_storage_identifier)
    ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
    ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
    label_schema_repo = LabelSchemaRepo(project_input.identifier)
    label_schema = label_schema_repo.get_latest()
    labels = label_schema.get_labels(include_empty=True)

    for i in range(number_of_images):
        name = f"image {i}"

        new_image_width = image_width() if callable(image_width) else image_width
        new_image_height = image_height() if callable(image_height) else image_height

        image_numpy, annotations = generate_random_annotated_image(
            image_width=new_image_width,
            image_height=new_image_height,
            labels=labels,
            max_shapes=max_shapes,
            min_size=min_size_shape,
            max_size=max_size_shape,
        )

        image_id = ImageRepo.generate_id()
        extension = ImageExtensions.PNG
        filename = f"{str(image_id)}{extension.value}"
        binary_filename = image_binary_repo.save(
            dst_file_name=filename,
            data_source=NumpyBinaryInterpreter.get_bytes_from_numpy(image_numpy=image_numpy, extension=extension.value),
        )
        size = image_binary_repo.get_object_size(binary_filename)

        # Make and save image
        image = Image(
            name=name,
            uploader_id="",
            id=image_id,
            width=new_image_width,
            height=new_image_height,
            size=size,
            extension=extension,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        image_repo.save(image)
        image_identifier = ImageIdentifier(image.id_)

        # Make and save annotation
        if "classification" in model_template_id.lower():
            for annotation in annotations:
                annotation.shape = Rectangle.generate_full_box()

        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=image_identifier,
            media_height=image.height,
            media_width=image.width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotations,
        )
        ann_scene_repo.save(annotation_scene)
        media_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
            annotation_scene=annotation_scene,
            project=project_input,
        )
        ann_scene_state_repo.save(media_state)

    for i in range(number_of_videos):
        generate_random_annotated_video(project=project_input, number_of_frames=60)

    if configurable_parameters is not None:
        configurable_parameters.workspace_id = project_input.workspace_id
        configurable_parameters.model_storage_id = ModelService.get_active_model_storage(
            project_identifier=project_input.identifier,
            task_node_id=project_input.get_trainable_task_nodes()[-1].id_,
        ).id_
        ConfigurableParametersRepo(project_input.identifier).save(configurable_parameters)

    return project_input, label_schema


def register_model_template_from_dict(
    test_case: FixtureRequest,
    model_template_desc: dict,
) -> ModelTemplate:
    model_template = ModelTemplateList().register_model_template(model_template_desc)

    model_template_id = model_template.model_template_id

    def cleanup():
        ModelTemplateList().unregister_model_template(model_template_id)

    test_case.addfinalizer(cleanup)

    return model_template


def register_model_template(
    test_case: FixtureRequest,
    task: type,
    model_template_id: str,
    model_template_path: str = "",
    task_type: str = "SEGMENTATION",
    task_family: str = "VISION",
    trainable: bool = False,
    improvements_based_on_compute_performance: bool = False,
) -> ModelTemplate:
    """
    Register a model template for testing purposes.

    The task will be automatically deleted from the register at the end of the test case.

    :param test_case: Current test case
    :param task: The task class
    :param model_template_id: name of the model template
    :param model_template_path: absolute path to the model template file
    :param task_type: The new name of the task
    :param task_family: The task family
    :param trainable: Set to True if the task is trainable
    :param improvements_based_on_compute_performance: Set to True if the task improvements should be evaluated
                                                      based on the results of compute_performance.
    :return: the newly created model template
    """
    model_template = {
        "task_family": task_family,
        "task_type": task_type,
        "model_template_id": model_template_id,
        "model_template_path": model_template_path,
        "name": model_template_id,
        "is_trainable": trainable,
        "task_type_sort_priority": 100,
        "instantiation": "CLASS",
        "entrypoints": {"base": task.__module__ + "." + task.__qualname__},
        "hyper_parameters": {"base_path": "hyper_parameters.yaml"},
    }

    return register_model_template_from_dict(test_case, model_template)


def verify_mongo_mapper(  # noqa: C901
    entity_to_map: MappableEntityType,
    mapper_class: MapperClassT,
    project: Project | None = None,
    dataset_storage: DatasetStorage | None = None,
    model_storage: ModelStorage | None = None,
    forward_parameters: Any = None,
    backward_parameters: Any = None,
    extend_forward_output: dict | None = None,
    compare_forward_maps: bool = True,
    compare_backward_maps: bool = True,
) -> tuple[dict, MappableEntityType]:
    """
    Check the correctness of a Mongo mapper.
    Given a mapper and a test object X performing these steps:
     1. Serialize X -> D
     2. Deserialize D -> X'
     3. Serialize X' -> D'
     4. Verify that X' == X
     5. Verify that D' == D

    :param entity_to_map: Test object to map. It is recommended to create it with
        non-default params, to guarantee that forward/backward are effectively tested
    :param mapper_class: Mongo mapper
    :param project: Project (if required by the mapper)
    :param dataset_storage: DatasetStorage (if required by the mapper)
    :param model_storage: ModelStorage (if required by the mapper)
    :param forward_parameters: Parameters for the forward mapping (if required)
    :param backward_parameters: Parameters for the backward mapping (if required)
    :param extend_forward_output: Dictionary of items to update the output of forward.
        Useful when some document fields are inserted outside of the MongoDB mapper.
    :param compare_forward_maps: Compare the serialized representations (D' == D)
    :param compare_backward_maps: Compare the original object with the
        deserialized one (X' == X)
    :return: Mapped and unmapped entities, in case any additional comparison needs
        to be performed outside this method.
    """
    # Build forward parameters
    forward_kwargs: dict[str, Any] = {}
    if issubclass(mapper_class, IMapperForward):
        pass
    elif issubclass(mapper_class, IMapperDatasetStorageForward):
        forward_kwargs["dataset_storage"] = dataset_storage
    elif issubclass(mapper_class, IMapperModelStorageForward):
        forward_kwargs["model_storage"] = model_storage
    elif issubclass(mapper_class, IMapperParametricForward):
        forward_kwargs["parameters"] = forward_parameters

    # Build backward parameters
    backward_kwargs: dict[str, Any] = {}
    if issubclass(mapper_class, IMapperBackward):
        pass
    elif issubclass(mapper_class, IMapperProjectIdentifierBackward):
        backward_kwargs["project_identifier"] = project.identifier  # type: ignore
    elif issubclass(mapper_class, IMapperDatasetStorageBackward):
        backward_kwargs["dataset_storage"] = dataset_storage
    elif issubclass(mapper_class, IMapperDatasetStorageIdentifierBackward):
        backward_kwargs["dataset_storage_identifier"] = dataset_storage.identifier  # type: ignore
    elif issubclass(mapper_class, IMapperModelStorageBackward):
        backward_kwargs["model_storage"] = model_storage
    elif issubclass(mapper_class, IMapperParametricBackward):
        backward_kwargs["parameters"] = backward_parameters

    logger.info("Forward arguments: %s; Backward arguments: %s", forward_kwargs, backward_kwargs)

    serialized_entity = mapper_class.forward(instance=entity_to_map, **forward_kwargs)  # type: ignore[union-attr]
    if extend_forward_output is not None:
        serialized_entity |= extend_forward_output
    # make a copy of the dictionary, in case the backward mapper extends it
    serialized_entity_frozen = deepcopy(serialized_entity)
    deserialized_entity = mapper_class.backward(instance=serialized_entity, **backward_kwargs)  # type: ignore[union-attr]
    reserialized_entity = mapper_class.forward(instance=deserialized_entity, **forward_kwargs)  # type: ignore[union-attr]
    if extend_forward_output is not None:
        reserialized_entity |= extend_forward_output

    if isinstance(entity_to_map, PersistentEntity):  # ignore ephemeral for testing
        deserialized_entity._ephemeral = entity_to_map.ephemeral

    if compare_forward_maps:
        compare(serialized_entity_frozen, reserialized_entity)
    if compare_backward_maps:
        compare(entity_to_map, deserialized_entity)

    return serialized_entity, deserialized_entity


def add_hyper_parameters_to_template(model_template_id: str, hyper_parameter_class: type[ConfigurableParameters]):
    """
    Add a hyper parameter schema to a previously registered model template. This
    function is used for testing purposes only.

    This function should be called when a model template is registered that is not
    backed by an actual template.yaml file. For the template to be used with custom
    hyper parameters, these parameters should first be added to the template via
    this function.

    :param model_template_id: name of the model template
    :param hyper_parameter_class: Class defining the hyper parameter schema (should
        be a subclass of ModelConfig)
    """
    model_template = ModelTemplateList().get_by_id(model_template_id)
    hyper_parameters = hyper_parameter_class(header="Custom hyper parameters")
    hyper_parameter_data = otx_config_helper.convert(hyper_parameters, dict, enum_to_str=True)
    model_template.hyper_parameters.manually_set_data_and_validate(hyper_parameter_data)
