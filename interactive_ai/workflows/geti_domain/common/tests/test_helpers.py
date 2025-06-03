# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import contextlib
import itertools
import logging
import math
import os
import random
import tempfile
import unittest
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import cast

import cv2
import numpy as np
import testfixtures.comparison
from bson import ObjectId
from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier, MediaIdentifierEntity, VideoFrameIdentifier
from iai_core.adapters.binary_interpreters import NumpyBinaryInterpreter
from iai_core.algorithms import ModelTemplateList
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.configuration.elements.default_model_parameters import DefaultModelParameters
from iai_core.configuration.elements.hyper_parameters import HyperParameters
from iai_core.configuration.elements.parameter_group import ParameterGroup, add_parameter_group
from iai_core.configuration.elements.primitive_parameters import (
    configurable_boolean,
    configurable_float,
    configurable_integer,
    string_attribute,
)
from iai_core.configuration.enums.model_lifecycle import ModelLifecycle
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind, NullAnnotationScene
from iai_core.entities.color import Color
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.image import Image
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema, NullLabelSchema
from iai_core.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from iai_core.entities.model import ModelConfiguration
from iai_core.entities.model_template import ModelTemplate
from iai_core.entities.project import Project
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Ellipse, Point, Polygon, Rectangle
from iai_core.entities.subset import Subset
from iai_core.entities.video import Video, VideoFrame
from iai_core.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    ConfigurableParametersRepo,
    DatasetRepo,
    LabelSchemaRepo,
    ProjectRepo,
    VideoRepo,
)
from iai_core.repos.storage.binary_repos import ImageBinaryRepo
from iai_core.services.model_service import ModelService
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.identifier_factory import IdentifierFactory
from iai_core.utils.media_factory import Media2DFactory
from iai_core.utils.project_factory import ProjectFactory
from pytest import FixtureRequest

from jobs_common_extras.evaluation.utils.segmentation_utils import create_annotation_from_segmentation_map

logger = logging.getLogger(__name__)


def compare_project(x, y, context):
    x.task_graph = x.task_graph
    y.task_graph = y.task_graph

    ignore_attributes = ["_Project__entity_cache"]
    return testfixtures.comparison.compare_object(x, y, context, ignore_attributes=ignore_attributes)


testfixtures.comparison.register(Project, compare_project)


def generate_random_annotated_image(  # noqa: C901
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
    keypoint_structure=None,
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
    :param keypoint_structure: Keypoint structure to assign to the project, only for Keypoint Detection projects
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
        keypoint_structure=keypoint_structure,
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


def generate_inference_dataset_of_all_media_in_project(project: Project) -> Dataset:
    """
    Generate the inference Dataset for all media entities in a given project.

    :param project: Project to generate inference Dataset for
    :return: Dataset
    """
    from iai_core.repos import ImageRepo, VideoRepo

    dataset_storage = project.get_training_dataset_storage()
    image_identifiers = [i.media_identifier for i in ImageRepo(dataset_storage.identifier).get_all()]
    video_identifiers = [v.media_identifier for v in VideoRepo(dataset_storage.identifier).get_all()]

    nested_video_frame_identifiers: Iterable[Iterable[MediaIdentifierEntity]] = [
        IdentifierFactory.expand_media_identifier(i, dataset_storage) for i in video_identifiers
    ]
    video_frame_identifiers = list(itertools.chain.from_iterable(nested_video_frame_identifiers))

    # Unfortunately Mypy does not support concatenating lists of different types
    # (ImageIdentifier and VideoFrameIdentifier) even though it is perfectly fine.
    # To workaround the issue, we cast the lists to List[MediaIdentifierEntity].
    media_identifiers = cast(list[MediaIdentifierEntity], video_frame_identifiers) + cast(
        list[MediaIdentifierEntity], image_identifiers
    )

    dataset_items = []
    for media_identifier in media_identifiers:
        annotation = NullAnnotationScene()
        media = Media2DFactory().get_media_for_identifier(
            media_identifier, dataset_storage_identifier=dataset_storage.identifier
        )
        image_identifier = media_identifier
        annotation.media_identifier = image_identifier
        dataset_items.append(DatasetItem(id_=DatasetRepo.generate_id(), media=media, annotation_scene=annotation))

    return Dataset(items=dataset_items, id=DatasetRepo.generate_id())


def generate_training_dataset_of_all_annotated_media_in_project(  # noqa: C901
    project: Project,
    seed: int | None = None,
    ignore_some_labels: bool = False,
) -> tuple[DatasetStorageIdentifier, Dataset]:
    """
    Generates a dataset for a project, with training, validation and testing subsets.
    Note: this function is intended for single task projects and may not work correctly for projects with
          taskchains with more than one deep-learning task.

    :param project: Project to create dataset for
    :param seed: random seed to use for making subset split (ignored if use_stratified_sampling is True)
    :param ignore_some_labels: If True, mark some labels within the item as ignored
    :return: generated Dataset
    """
    from iai_core.repos import AnnotationSceneRepo, ImageRepo, VideoRepo

    dataset_storage = project.get_training_dataset_storage()
    ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
    image_repo = ImageRepo(dataset_storage.identifier)
    video_repo = VideoRepo(dataset_storage.identifier)

    # Consume/copy cursors
    images = list(image_repo.get_all())
    videos = list(video_repo.get_all())

    dataset_items = []
    annotations = ann_scene_repo.get_latest_annotations_by_kind_and_identifiers(
        [ImageIdentifier(image.id_) for image in images], AnnotationSceneKind.ANNOTATION
    )
    for image, annotation in zip(images, annotations):
        if not isinstance(annotation, NullAnnotationScene):
            labels_to_ignore = []
            if ignore_some_labels and len(label_set := annotation.get_label_ids()):
                label_id = next(iter(label_set))
                labels_to_ignore = [label_id]
            dataset_items.append(
                DatasetItem(
                    id_=DatasetRepo.generate_id(),
                    media=image,
                    annotation_scene=annotation,
                    ignored_label_ids=labels_to_ignore,
                )
            )

    for video in videos:
        annotations = ann_scene_repo.get_latest_annotations_by_kind_and_media_id(
            media_id=video.id_, annotation_kind=AnnotationSceneKind.ANNOTATION
        )
        for annotation in annotations:
            if not isinstance(annotation, NullAnnotationScene) and isinstance(
                annotation.media_identifier, VideoFrameIdentifier
            ):
                labels_to_ignore = (
                    list(annotation.get_label_ids())[:1] if ignore_some_labels else []
                )  # ignore the first label
                dataset_items.append(
                    DatasetItem(
                        media=VideoFrame(video, annotation.media_identifier.frame_index),
                        annotation_scene=annotation,
                        ignored_label_ids=labels_to_ignore,
                        id_=DatasetRepo.generate_id(),
                    )
                )

    # Use a local rng device to prevent the seed from affecting code outside this function
    rng = random.Random(seed)

    rng.shuffle(dataset_items)
    dataset_length = len(dataset_items)
    for i, _row in enumerate(dataset_items):
        subset_region = i / dataset_length
        if subset_region >= 0.8:
            subset = Subset.TESTING
        elif subset_region >= 0.6:
            subset = Subset.VALIDATION
        else:
            subset = Subset.TRAINING
        dataset_items[i].subset = subset

    return dataset_storage.identifier, Dataset(items=dataset_items, id=DatasetRepo.generate_id())


def generate_and_save_random_simple_segmentation_project(
    request: FixtureRequest,
    projectname: str,
) -> Project:
    """
    Creates simple segmentation project in the default workspace, with one image per
    label. The project contains 10 annotated images:
    5 with circles of size 50, 4 with triangles of size 20, one empty image.
    The task is a mock segmentation task.
    The project, images and annotations are saved to their repositories.

    :param request: pytest Request
    :param projectname: Name of the project that is created
    """
    from iai_core.repos import AnnotationSceneRepo, ImageRepo, ProjectRepo

    register_model_template(request, type(None), "segmentation", "SEGMENTATION", trainable=True)
    project = ProjectFactory().create_project_single_task(
        name=projectname,
        description="",
        creator_id="",
        labels=[
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ],
        model_template_id="segmentation",
    )
    dataset_storage = project.get_training_dataset_storage()
    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=project.workspace_id,
        project_id=project.id_,
        dataset_storage_id=dataset_storage.id_,
    )
    label_schema_repo = LabelSchemaRepo(project.identifier)
    project_label_schema = label_schema_repo.get_latest()
    ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
    ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)

    for i in range(10):
        # The first 9 images contain shapes: 5 circles, 4 triangles. The last image is empty.
        mask = None
        shapename = ""
        if i < 9:
            if i < 5:
                shapename = "ellipse"
            else:
                shapename = "triangle"

            imdata = (np.random.standard_normal([256, 256, 3]) * 255).astype(np.uint8)

            mask = imdata.copy().astype(np.float64)[:, :, 0]
            mask[mask == 255] = 0
            mask[mask != 0] = 1 if shapename == "ellipse" else 2
            soft_prediction = mask / 2
        else:
            imdata = np.zeros((256, 256, 3), dtype=np.uint8)

        image_binary_repo = ImageBinaryRepo(dataset_storage.identifier)

        image_id = ImageRepo.generate_id()
        extension = ImageExtensions.JPG
        filename = f"{str(image_id)}{extension.value}"
        binary_filename = image_binary_repo.save(
            dst_file_name=filename,
            data_source=NumpyBinaryInterpreter.get_bytes_from_numpy(image_numpy=imdata, extension=extension.value),
        )
        size = image_binary_repo.get_object_size(binary_filename)

        image = Image(
            name=f"{shapename}{i}",
            uploader_id="",
            extension=ImageExtensions.JPG,
            id=ImageRepo.generate_id(),
            width=imdata.shape[1],
            height=imdata.shape[0],
            size=size,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        ImageRepo(dataset_storage.identifier).save(image)
        image_identifier = ImageIdentifier(image_id=image.id_)

        annotation = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=image_identifier,
            media_height=image.height,
            media_width=image.width,
            id_=AnnotationSceneRepo.generate_id(),
        )
        if i < 9 and mask is not None:  # add annotation for non-empty images
            project_labels = project_label_schema.get_labels(include_empty=True)
            labeldict = {1: project_labels[0], 2: project_labels[1]}
            annotations = create_annotation_from_segmentation_map(
                hard_prediction=mask,
                soft_prediction=soft_prediction,
                label_map=labeldict,
            )
            annotation.append_annotations(annotations)
        ann_scene_repo.save(annotation)
        media_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
            annotation_scene=annotation, project=project
        )
        ann_scene_state_repo.save(media_state)
    ProjectRepo().save(project)
    return project


def empty_model_configuration() -> ModelConfiguration:
    return ModelConfiguration(DefaultModelParameters(), NullLabelSchema())


def assert_almost_equal(first, second, delta=None, places=None, msg=None):
    if first == second:
        return
    if msg is not None:
        if delta is not None:
            assert math.isclose(first, second, abs_tol=delta), msg
        if places is None:
            places = 7
        assert math.isclose(first, second, abs_tol=0.1**places), msg
    else:
        if delta is not None:
            assert math.isclose(first, second, abs_tol=delta)
        if places is None:
            places = 7
        assert math.isclose(first, second, abs_tol=0.1**places)


class TestProject:
    def __init__(self, project, dataset, segmentation_model, circle_dataset, triangle_dataset) -> None:
        self.project = project
        self.dataset = dataset
        self.segmentation_model = segmentation_model
        self.circle_dataset = circle_dataset
        self.triangle_dataset = triangle_dataset
        self.empty_dataset_item = [item for item in dataset if len(item.annotation_scene.get_label_ids()) == 0][0]


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


def create_empty_segmentation_project(
    test_case: FixtureRequest,
) -> Project:
    """
    Create an empty segmentation project
    """
    register_model_template(
        test_case=test_case,
        task=type(None),
        model_template_id="torch_segmentation",
        task_type="SEGMENTATION",
        trainable=True,
    )
    project = ProjectFactory().create_project_single_task(
        name="test segmentation",
        description="test segmentation",
        creator_id="",
        labels=[
            {"name": "label1", "color": "#00ff00ff"},
        ],
        model_template_id="torch_segmentation",
    )

    if test_case is not None:
        if isinstance(test_case, unittest.TestCase):
            test_case.addCleanup(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))
        else:
            test_case.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))
    return project


class LabelSchemaExample:
    def __init__(self) -> None:
        self.label_domain = Domain.CLASSIFICATION

        self.flowering = self.new_label_by_name("flowering")
        self.no_plant = self.new_label_by_name("no_plant")
        self.vegetative = self.new_label_by_name("vegetative")

    def new_label_by_name(self, name: str, is_empty: bool = False) -> Label:
        label = Label(
            id_=ID(name),
            name=name,
            domain=self.label_domain,
            color=Color.random(),
            is_empty=is_empty,
        )
        label.id_ = ID(ObjectId())
        return label

    def add_hierarchy(self, label_schema: LabelSchema) -> tuple[Label, Label, Label]:
        """Adds children to flowering, no_plant and vegetative"""
        label_schema.add_group(
            LabelGroup(
                "plant_state",
                [self.flowering, self.no_plant, self.vegetative],
                LabelGroupType.EXCLUSIVE,
            )
        )
        flower_partial_visible = self.new_label_by_name("flower_partial_visible")
        flower_fully_visible = self.new_label_by_name("flower_fully_visible")
        label_schema.add_group(
            LabelGroup(
                "flowering_state",
                [flower_fully_visible, flower_partial_visible],
                LabelGroupType.EXCLUSIVE,
            )
        )
        label_schema.add_child(self.flowering, flower_partial_visible)
        label_schema.add_child(self.flowering, flower_fully_visible)

        assert self.flowering == label_schema.get_parent(flower_partial_visible)
        assert label_schema.get_parent(self.no_plant) is None

        few_leaves = self.new_label_by_name("few_leaves")
        label_schema.add_group(LabelGroup("leaf_state", [few_leaves], LabelGroupType.EXCLUSIVE))
        label_schema.add_child(self.vegetative, few_leaves)
        return few_leaves, flower_fully_visible, flower_partial_visible


@contextlib.contextmanager
def generate_random_single_image(width: int = 480, height: int = 360) -> Iterator[str]:
    """
    Generates a random image, cleans up automatically if used in a `with` statement
    :param width: Width of the image. Defaults to 480.
    :param height: Height of the image. Defaults to 360.

    :return: Path to an image file
    """

    temp_dir = tempfile.TemporaryDirectory()
    temp_file = os.path.join(temp_dir.name, "temp_image.jpg")
    _write_random_image(width, height, temp_file)

    try:
        yield temp_file
    finally:
        temp_dir.cleanup()


def _write_random_image(width: int, height: int, filename: str):
    img = np.uint8(np.random.random((height, width, 3)) * 255)
    cv2.imwrite(filename, img)  # type: ignore[call-overload]


class ConfigExample(ConfigurableParameters):
    header = string_attribute("Test configuration for an object detection task")
    description = header

    class __LearningParameters(ParameterGroup):
        header = string_attribute("Test Learning Parameters")
        description = header

        batch_size = configurable_integer(
            default_value=5,
            min_value=1,
            max_value=512,
            header="Test batch size",
            description="The number of training samples seen in each iteration of training. Increasing this value "
            "improves training time and may make the training more stable. A larger batch size has higher "
            "memory requirements.",
            warning="Increasing this value may cause the system to use more memory than available, "
            "potentially causing out of memory errors, please update with caution.",
            affects_outcome_of=ModelLifecycle.TRAINING,
        )

        num_iters = configurable_integer(
            default_value=1,
            min_value=1,
            max_value=100000,
            header="Number of training iterations",
            description="Increasing this value causes the results to be more robust but training time will be longer.",
            affects_outcome_of=ModelLifecycle.TRAINING,
        )

        learning_rate = configurable_float(
            default_value=0.01,
            min_value=1e-07,
            max_value=1e-01,
            header="Learning rate",
            description="Increasing this value will speed up training convergence but might make it unstable.",
            affects_outcome_of=ModelLifecycle.TRAINING,
        )

        learning_rate_warmup_iters = configurable_integer(
            default_value=100,
            min_value=1,
            max_value=10000,
            header="Number of iterations for learning rate warmup",
            description="Test learning rate warmup",
            affects_outcome_of=ModelLifecycle.TRAINING,
        )

        num_workers = configurable_integer(
            default_value=4,
            min_value=2,
            max_value=10,
            header="num_workers test header",
            description="num_workers test description",
            affects_outcome_of=ModelLifecycle.NONE,
        )

    class __Postprocessing(ParameterGroup):
        header = string_attribute("Test Postprocessing")
        description = header

        result_based_confidence_threshold = configurable_boolean(
            default_value=True,
            header="Test Result based confidence threshold",
            description="Test confidence threshold is derived from the results",
            affects_outcome_of=ModelLifecycle.INFERENCE,
        )

        confidence_threshold = configurable_float(
            default_value=0.25,
            min_value=0,
            max_value=1,
            header="Test Confidence threshold",
            description="This threshold only takes effect if the threshold is not set based on the result.--Only test",
            affects_outcome_of=ModelLifecycle.INFERENCE,
        )

    learning_parameters = add_parameter_group(__LearningParameters)
    postprocessing = add_parameter_group(__Postprocessing)
