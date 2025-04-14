# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
import os
import tempfile
import unittest
from collections.abc import Callable, Sequence

import cv2
import numpy as np
import testfixtures.comparison
from geti_types import DatasetStorageIdentifier, ImageIdentifier, VideoFrameIdentifier
from pytest import FixtureRequest
from sc_sdk.adapters.binary_interpreters import NumpyBinaryInterpreter
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Label
from sc_sdk.entities.label_schema import LabelSchema
from sc_sdk.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from sc_sdk.entities.model_template import ModelTemplate
from sc_sdk.entities.project import Project
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Ellipse, Point, Polygon, Rectangle
from sc_sdk.entities.video import Video
from sc_sdk.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    ConfigurableParametersRepo,
    LabelSchemaRepo,
    ProjectRepo,
    VideoRepo,
)
from sc_sdk.repos.storage.binary_repos import ImageBinaryRepo
from sc_sdk.services.model_service import ModelService
from sc_sdk.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.project_factory import ProjectFactory

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
            low=[min_size, min_size], high=[min(max_size, image_width - rx), min(max_size, image_height - ry)]
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
    from sc_sdk.repos import AnnotationSceneRepo, ImageRepo

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
