# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import itertools
import os
import tempfile
import zipfile
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from shutil import copyfile, copytree, make_archive
from typing import NamedTuple, cast

import cv2
import numpy as np
import pkg_resources
from datumaro import AnnotationType as dm_AnnotationType
from datumaro import Bbox as dm_Bbox
from datumaro import Dataset as dm_Dataset
from datumaro import Ellipse as dm_Ellipse
from datumaro import Image as dm_Image
from datumaro import Label as dm_Label
from datumaro import LabelCategories as dm_LabelCategories
from datumaro import Mask as dm_Mask
from datumaro import Points as dm_Points
from datumaro import PointsCategories as dm_PointsCategories
from datumaro import Polygon as dm_Polygon
from datumaro import Video as dm_Video
from datumaro import VideoFrame as dm_VideoFrame
from datumaro.components.annotation import NO_GROUP
from geti_types import (
    ID,
    DatasetStorageIdentifier,
    ImageIdentifier,
    MediaIdentifierEntity,
    ProjectIdentifier,
    VideoFrameIdentifier,
    VideoIdentifier,
)
from iai_core.adapters.binary_interpreters import NumpyBinaryInterpreter
from iai_core.algorithms import ModelTemplateList
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset
from iai_core.entities.image import Image
from iai_core.entities.label import Label
from iai_core.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from iai_core.entities.model_template import ModelTemplate
from iai_core.entities.project import Project
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Ellipse, Keypoint, Point, Polygon, Rectangle
from iai_core.entities.video import Video, VideoFrame
from iai_core.entities.video_annotation_range import RangeLabels, VideoAnnotationRange
from iai_core.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    DatasetRepo,
    ImageRepo,
    LabelSchemaRepo,
    ProjectRepo,
    VideoAnnotationRangeRepo,
    VideoRepo,
)
from iai_core.repos.base import SessionBasedRepo
from iai_core.repos.storage.binary_repos import ImageBinaryRepo, ThumbnailBinaryRepo
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from jobs_common_extras.datumaro_conversion.definitions import SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES, GetiProjectType
from jobs_common_extras.datumaro_conversion.mappers.id_mapper import VideoNameIDMapper
from jobs_common_extras.datumaro_conversion.sc_extractor import RangeIdentifier
from pytest import FixtureRequest

from job.repos.data_repo import ImportDataRepo
from job.utils.constants import MIN_VIDEO_SIZE
from job.utils.import_utils import ImportUtils
from tests.fixtures.datasets import AnnotationDefinition, DatasetDefinition


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


@dataclass
class ScDatasetItem:
    id_: ID
    media: Image | Video | VideoFrame
    annotation_scene: AnnotationScene


def generate_polygon_shape() -> Polygon:
    """
    Generate polygon shape of three points

    :return: polygon entity
    """
    points = [Point(0.0, 0.0), Point(0.5, 1.0), Point(1.0, 0.0)]
    return Polygon(points=points)


def generate_rectangle_shape() -> Rectangle:
    """
    Generate rectangle shape

    :return: rectangle entity
    """
    return Rectangle(x1=0.2, y1=0.3, x2=0.8, y2=0.7)


def generate_ellipse_shape() -> Ellipse:
    """
    Generate ellipse shape

    :return: ellipse entity
    """
    return Ellipse(x1=0.2, y1=0.3, x2=0.8, y2=0.7)


def generated_rotated_rectangle_shape() -> Polygon:
    """
    Generate rotated rectangle shape

    :return: polygon entity
    """
    points = [
        Point(301.94, 296.62),
        Point(284.38, 272.52),
        Point(468.52, 138.33),
        Point(486.08, 162.43),
    ]
    return Polygon(points=points)


def generate_keypoint_shape() -> Keypoint:
    """
    Generate keypoint shape

    :return: polygon entity
    """
    return Keypoint(x=0.2, y=0.3, is_visible=True)


def generate_images_and_annotation_scenes(
    project: Project,
    num_annotated_images: int,
    num_unannotated_images: int,
    num_empty_annotated_images: int = 0,
    labels: list[Label] | None = None,
    empty_labels: list[Label] | None = None,
    label_groups: list[list[Label]] | None = None,
    shape_generator: Callable | None = None,
    shape_generators: dict[str, Callable] | None = None,
    duplicate_image_name: bool = False,
) -> tuple[list[Image], list[AnnotationScene]]:
    """
    Generate a number of images and annotation scenes

    :param project: project to contain images and annotation scenes
    :param num_annotated_images: number of images with annotation scenes to create
    :param num_unannotated_images: number of images without annotation scenes to create
    :param num_empty_annotated_images: number of images with empty annotation
    :param labels: list of labels which can be in the annotations
    :param empty_labels: list of empty labels
    :param label_groups: if provided, labels are added in groups to each annotation
    :param shape_generator: callable used to generate shapes in the annotation scenes
    :param shape_generators: mapping of labels to shape generator functions
    :param duplicate_image_name: If the image names should be unique or not. If false,
        then the images will be named incrementally "image_0", "image_1", ..., otherwise
        if true, then each image will be named "image"
    :return: list of images, list of annotation scenes
    """
    dataset_storage = project.get_training_dataset_storage()
    project_labels = get_project_labels(project=project, include_empty=True)
    label_map = {label.id_: label for label in project_labels}
    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=project.workspace_id,
        project_id=project.id_,
        dataset_storage_id=dataset_storage.id_,
    )
    ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
    image_repo = ImageRepo(dataset_storage_identifier)
    image_binary_repo = ImageBinaryRepo(dataset_storage_identifier)

    if not empty_labels:
        num_empty_annotated_images = 0
        empty_labels = []
    num_images = num_annotated_images + num_unannotated_images + num_empty_annotated_images
    images = []
    ann_scenes = []
    for i in range(num_images):
        if labels is not None:
            label_idx = i % len(labels)
            scored_labels = [
                ScoredLabel(
                    label_id=labels[label_idx].id_,
                    is_empty=labels[label_idx].is_empty,
                    probability=1.0,
                )
            ]
        elif label_groups is not None:
            label_idx = i % len(label_groups)
            scored_labels = [
                ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)
                for label in label_groups[label_idx]
            ]
        else:
            raise ValueError("Either 'labels' or 'label_groups' arg must be provided")
        image_name = "image" if duplicate_image_name else f"image_{i}"
        image_id = ImageRepo.generate_id()
        width = 100
        height = 100
        extension = ImageExtensions.JPG
        image_numpy = np.full((height, width, 3), 255, dtype=np.uint8)
        filename = f"{str(image_id)}{extension.value}"
        binary_filename = image_binary_repo.save(
            dst_file_name=filename,
            data_source=NumpyBinaryInterpreter.get_bytes_from_numpy(image_numpy=image_numpy, extension=extension.value),
        )
        size = image_binary_repo.get_object_size(binary_filename)
        image = Image(
            name=image_name,
            uploader_id="",
            extension=extension,
            id=image_id,
            width=width,
            height=height,
            size=size,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        image_repo.save(image)
        if i < num_annotated_images:
            if shape_generator is not None:
                shape = shape_generator()
            elif shape_generators is not None:
                shape = shape_generators[label_map[scored_labels[-1].label_id].name]()  # last one
            else:
                raise ValueError("Either 'shape_generator' or 'shape_generators' arg must be provided")
            ann_scene = AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=ImageIdentifier(image.id_),
                media_height=image.height,
                media_width=image.width,
                id_=AnnotationSceneRepo.generate_id(),
                annotations=[Annotation(shape=shape, labels=scored_labels)],
            )
            ann_scene_repo.save(ann_scene)
            images.append(image)
            ann_scenes.append(ann_scene)

        elif i < num_annotated_images + num_empty_annotated_images:
            empty_annotation = Annotation(
                Rectangle.generate_full_box(),
                labels=[
                    ScoredLabel(label_id=empty_label.id_, is_empty=True, probability=1) for empty_label in empty_labels
                ],
            )
            ann_scene = AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=ImageIdentifier(image.id_),
                media_height=image.height,
                media_width=image.width,
                id_=AnnotationSceneRepo.generate_id(),
                annotations=[empty_annotation],
            )
            ann_scene_repo.save(ann_scene)
            images.append(image)
            ann_scenes.append(ann_scene)

    return images, ann_scenes


def _generate_random_video(
    video_path: str,
    fps: float,
    width: int,
    height: int,
    number_of_frames: int,
    labels: list[Label],
    is_global_or_anomaly: bool,
) -> tuple[list[RangeLabels], list[list[Annotation]]]:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
    video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    range_labels = []
    annotations_per_frame = []  # List with list of annotations
    # Generate frames and annotations
    if is_global_or_anomaly:
        image_shape = (height, width, 3)
        img = np.full(image_shape, 255, dtype=np.uint8)
        partitions = np.array_split(range(number_of_frames), len(labels))
        for i, partition in enumerate(partitions):
            if len(partition) == 0:
                continue
            scored_label = ScoredLabel(label_id=labels[i].id_, is_empty=labels[i].is_empty, probability=1.0)
            annotation = Annotation(Rectangle.generate_full_box(), labels=[scored_label])
            for _ in partition:
                annotations_per_frame.append([annotation])
                video_writer.write(img)
            range_labels.append(
                RangeLabels(
                    start_frame=partition[0],
                    end_frame=partition[-1],
                    label_ids=[scored_label.label_id],
                )
            )
    else:
        min_size = min(30, min(width, height))
        for i in range(number_of_frames):
            img, annotations = generate_random_annotated_image(
                image_width=width,
                image_height=height,
                labels=labels,
                min_size=min_size,
            )
            annotations_per_frame.append(annotations)
            video_writer.write(img)
    video_writer.release()

    return range_labels, annotations_per_frame


def generate_random_video(
    project: Project,
    video_name: str = "Generated video",
    width: int = MIN_VIDEO_SIZE,
    height: int = MIN_VIDEO_SIZE,
    number_of_frames: int = 10,
    generate_annotations: bool = True,
) -> tuple[Video, list[AnnotationScene]]:
    """
    Generate a random video that is `number_of_frames` frames at 30 fps for `project`.
    Video contains random shapes on white background.

    :param project: Project that the Video will added to
    :param width: Width of the video
    :param height: Height of the video
    :param number_of_frames: Amount of frames to generate
    :param generate_annotations: Whether to generate annotations or not.
                                 This will be ignored(set as True) for anomaly tasks.
    :return: Tuple(Video entity, list of AnnotationScene entities)
    """
    dataset_storage = project.get_training_dataset_storage()
    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=project.workspace_id,
        project_id=project.id_,
        dataset_storage_id=dataset_storage.id_,
    )
    ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
    ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)
    video_repo = VideoRepo(dataset_storage_identifier)

    # VideoAnnotationRange is supported only for a single global/anomaly task projects
    tasks = project.get_trainable_task_nodes()
    is_global_or_anomaly: bool = len(tasks) == 1 and (
        tasks[0].task_properties.is_global or tasks[0].task_properties.is_anomaly
    )
    if not generate_annotations and tasks[0].task_properties.is_anomaly:
        generate_annotations = True

    # Video path will be made from the video id and stored in the temp directory
    tmp_dir = tempfile.gettempdir()
    video_id = video_repo.generate_id()
    extension = ".mp4"
    video_path = os.path.join(tmp_dir, video_id + extension)

    project_identifier = ProjectIdentifier(project_id=project.id_, workspace_id=project.workspace_id)
    label_schema_repo: LabelSchemaRepo = LabelSchemaRepo(project_identifier)
    project_label_schema = label_schema_repo.get_latest()
    labels = project_label_schema.get_labels(include_empty=False)
    fps = 30.0
    range_labels, annotations_per_frame = _generate_random_video(
        video_path, fps, width, height, number_of_frames, labels, is_global_or_anomaly
    )
    # Generate video
    filename = video_repo.binary_repo.save(dst_file_name=video_path, data_source=video_path)
    size = video_repo.binary_repo.get_object_size(filename)

    try:
        video_extension = VideoExtensions[extension[1:].upper()]
    except KeyError:
        video_extension = VideoExtensions.MP4

    video = Video(
        name=video_name,
        stride=2,  # to check all annotated frames would be exported
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
    VideoRepo(dataset_storage.identifier).save(video)

    # Save annotations
    annotation_scenes = []
    if generate_annotations:
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

        if is_global_or_anomaly and range_labels:
            range_repo = VideoAnnotationRangeRepo(dataset_storage_identifier)
            ann_range = VideoAnnotationRange(
                video_id=video.id_,
                range_labels=range_labels,
                id_=VideoAnnotationRangeRepo.generate_id(),
            )
            range_repo.save(ann_range)

    return video, annotation_scenes


def get_voc_global_labels_map(voc_dataset_path: str, label_names: Iterable[str]) -> dict[str, set[str]]:
    """
    get mapping of image name to set of global labels for that image for all images in
    voc dataset

    :param voc_dataset_path: path of voc dataset
    :param label_names: list of label names in voc dataset
    :return: mapping of image name to set of global labels appearing in that image
    """
    exported_image_label_map: dict[str, set] = {}
    annotation_dataset_dir = os.path.join(voc_dataset_path, "ImageSets", "Main")
    filenames = os.listdir(annotation_dataset_dir)

    # default.txt contains the names of all the images, either annotated or not
    image_names_file_path = os.path.join(annotation_dataset_dir, "default.txt")
    with open(image_names_file_path) as file:
        all_images_names = {line.strip() for line in file.readlines()}
    for image_name in all_images_names:
        exported_image_label_map[image_name] = set()

    for label_name in label_names:
        label_filename = [fn for fn in filenames if fn.startswith(label_name + "_")][0]
        label_file_path = os.path.join(annotation_dataset_dir, label_filename)
        with open(label_file_path) as file:
            for line in file:
                # format is: <label_name> <present(1/-1)>
                data = line.strip().split(" ")
                image_name = data[0]
                label_presence = data[-1]
                if label_presence == "1":
                    exported_image_label_map[image_name].add(label_name)
    return exported_image_label_map


def get_datumaro_labels_map(dm_dataset_path: str) -> dict[str, set[str]]:
    """
    get mapping of image name to set of global labels for that image for all images in Datumaro dataset

    :param dataset: path to Datumaro dataset
    :return: mapping of image name to set of global labels names appearing in that image
    """
    dm_dataset = dm_Dataset.import_from(dm_dataset_path, format="datumaro")
    return get_dm_labels_map(dm_dataset)


def get_datumaro_exportor_version(dm_dataset_path: str) -> str:
    """
    get Geti-Datumaro exportor version

    :param: dm_dataset_path: path to Datumaro dataset
    :return: version string
    """
    dm_dataset = dm_Dataset.import_from(dm_dataset_path, format="datumaro")
    return dm_dataset.infos().get("ScExtractorVersion", "")


def get_sc_labels(
    dataset_storage: DatasetStorage,
    dataset: list[ScDatasetItem],
    include_empty: bool = False,
) -> list[Label]:
    project_identifier = ProjectIdentifier(
        project_id=dataset_storage.project_id, workspace_id=dataset_storage.workspace_id
    )
    latest_schema = LabelSchemaRepo(project_identifier).get_latest()
    label_map = {label.id_: label for label in latest_schema.get_labels(include_empty=include_empty)}
    label_id_set = set(
        itertools.chain.from_iterable(item.annotation_scene.get_label_ids(include_empty) for item in dataset)
    )
    return [label_map[label_id] for label_id in label_id_set]


def get_sc_labels_map(dataset_storage: DatasetStorage, dataset: Dataset | list[ScDatasetItem]) -> dict[str, set[str]]:
    """
    get mapping of image name to set of global labels for that image for all images in
    SC dataset

    :param dataset: Sc dataset
    :return: mapping of image name to set of global labels appearing in that image
    """
    sc_image_label_map = {}
    project_identifier = ProjectIdentifier(
        project_id=dataset_storage.project_id, workspace_id=dataset_storage.workspace_id
    )
    latest_schema = LabelSchemaRepo(project_identifier).get_latest()
    label_map = {label.id_: label for label in latest_schema.get_labels(include_empty=True)}
    for item in dataset:
        ann_scene = item.annotation_scene
        label_ids = ann_scene.get_label_ids()
        labels = {label_map[label_id].name for label_id in label_ids}
        media = item.media
        if isinstance(media, VideoFrame):
            media_name = f"{media.name}_frame_{media.frame_index}"
        else:
            media_name = media.name
        sc_image_label_map[media_name] = labels
    return sc_image_label_map


def get_dm_labels_map(dm_dataset: dm_Dataset) -> dict[str, set[str]]:
    """
    get mapping of image name to set of global labels for that image for all images in
    SC dataset

    :param dataset: Sc dataset
    :return: mapping of image name to set of global labels appearing in that image
    """
    dm_image_label_map = {}
    dm_label_mapping = dm_dataset.categories()[dm_AnnotationType.label]
    for dm_item in dm_dataset:
        if isinstance(dm_item.media, dm_Image | dm_VideoFrame):
            dm_image_label_map[dm_item.id] = {dm_label_mapping[annon.label].name for annon in dm_item.annotations}
        elif isinstance(dm_item.media, dm_Video) and ImportUtils.is_video_unannotated(dm_item):
            dm_image_label_map[dm_item.id] = set()

    return dm_image_label_map


def get_project_labels(project: Project, include_empty: bool = False) -> list[Label]:
    """
    get all labels in an SC project

    :param project: SC project
    :param include_empty: includes empty labels
    :return: list of labels in project
    """
    project_identifier = ProjectIdentifier(project_id=project.id_, workspace_id=project.workspace_id)
    latest_schema = LabelSchemaRepo(project_identifier).get_latest()
    labels = cast(list[Label], latest_schema.get_labels(include_empty=include_empty))
    return labels


def get_media_ann_scenes_from_project_id(
    project_id: ID,
    dataset_id: ID | None = None,
) -> tuple[list[Image], list[Video], list[AnnotationScene]]:
    """
    Get images and annotation scenes from project id

    :param project_id: id of the project
    :param dataset_id: id of the dataset
    :return: list of images, list of annotation scenes
    """
    project = ProjectRepo().get_by_id(project_id)
    if dataset_id is not None:
        dataset_storage = project.get_dataset_storage_by_id(dataset_id)
    else:
        dataset_storage = project.get_training_dataset_storage()
    images = list(ImageRepo(dataset_storage.identifier).get_all())
    videos = list(VideoRepo(dataset_storage.identifier).get_all())
    annotation_scenes = list(AnnotationSceneRepo(dataset_storage.identifier).get_all())
    return images, videos, annotation_scenes


def get_label_maps(project: Project, dm_label_names: list[str], map_empty_label: bool = False) -> dict[str, Label]:
    """
    Generate a dummy label_maps that maps from datumaro label_name to sc_label

    :param project: the target project to map the sc_label
    :param dm_label_names: label names of dm dataset for mapping
    :param map_empty_label: Maps empty sc label to the first dm label if True
    :return: A dictionary to map from datumaro label_name to sc_label
    """
    # Get list of Label() in the project
    sc_labels = get_project_labels(project=project, include_empty=False)
    assert len(sc_labels) > 0
    assert len(dm_label_names) > 0

    # Generate labels_map that maps from datumaro label_name to project Label
    labels_map = {}
    for i, dm_label_name in enumerate(dm_label_names):
        labels_map[dm_label_name] = sc_labels[i % len(sc_labels)]

    if map_empty_label:
        sc_labels = get_project_labels(project=project, include_empty=True)
        empty_label = None
        for sc_label in sc_labels:
            if sc_label.is_empty:
                empty_label = sc_label
                break
        if empty_label is not None:
            labels_map[dm_label_names[0]] = empty_label

    return labels_map


def return_none(*args, **kwargs) -> None:
    return None


def get_dm_dataset_definition(  # noqa: C901
    dm_dataset: dm_Dataset,
    label_names: list[str],
) -> DatasetDefinition:
    """
    Convert dm_dataset to a dataset definition.
    For examples of dataset definitions, see dataset definition fixtures

    :param dm_dataset: Imported datumaro dataset
    :param label_names: list of label names
    :return: dataset definition representing SC annotation scenes
    """
    dataset_definition: DatasetDefinition = {}
    label_cat: dm_LabelCategories = dm_dataset.categories()[dm_AnnotationType.label]
    points_cat: dm_PointsCategories = dm_dataset.categories().get(dm_AnnotationType.points, None)

    # assumption: there's only one keypoints set in the dataset.
    point_labels = points_cat.items[0].labels if points_cat is not None else None
    label_to_idx = {}
    for idx, label_name in enumerate(label_names):
        if point_labels is None:
            label, _ = label_cat.find(label_name)
        else:
            label = point_labels.index(label_name)
        label_to_idx[label] = idx

    for item in dm_dataset:
        if isinstance(item.media, dm_Video) and not ImportUtils.is_video_unannotated(item):
            continue  # VideoAnnotationRange
        if not isinstance(item.media, dm_Image | dm_VideoFrame | dm_Video):
            continue  # unsupported media type
        # 'group' of Datumaro annotations
        # some data-format, e.g. COCO, allows multiple annotation formats for an annotation.
        # e.g.) an annotation for an item may have both bbox and polygon formats labeling the same target.
        # In this case, Datumaro groups them by the 'group' attribute.
        # This means that len(dm_anns_group_by) is equal to # of annotation for dm_item
        anns_group_by = defaultdict(list)
        for ann in item.annotations:
            anns_group_by[ann.group].append(ann)
        valid_anns = []
        for group, anns in anns_group_by.items():
            # all annotations with 'group == NO_GROUP' annotates the independent labeling object.
            if group == NO_GROUP:
                valid_anns += anns
                continue
            # Since Geti doesn't have 'group' like concept,
            # we filter-out bbox annotation
            # if both bbox and polygon annotation types grouped together.
            bbox_anns = []
            has_polygon = False
            for ann in anns:
                if isinstance(ann, dm_Polygon | dm_Mask | dm_Ellipse):
                    has_polygon = True
                elif isinstance(ann, dm_Bbox):
                    bbox_anns.append(ann)
            if has_polygon and len(bbox_anns) > 0:
                for bbox_ann in bbox_anns:
                    anns.remove(bbox_ann)
            valid_anns += anns

        dataset_item_definition: AnnotationDefinition = []
        for ann in valid_anns:
            if point_labels:
                if isinstance(ann, dm_Points):
                    # we need to set visibility as label
                    label = [0] * len(label_names)
                    for point_label, visibility in enumerate(ann.visibility):
                        label[label_to_idx[point_label]] = visibility.value
                    dataset_item_definition.append(("points", tuple(label)))
                elif isinstance(ann, dm_Bbox):
                    dataset_item_definition.append(("bbox", 0))
            else:
                label_idx = label_to_idx[ann.label]
                if isinstance(ann, dm_Label):
                    dataset_item_definition.append(("label", label_idx))
                elif isinstance(ann, dm_Bbox):
                    dataset_item_definition.append(("bbox", label_idx))
                elif isinstance(ann, dm_Polygon):
                    dataset_item_definition.append(("polygon", label_idx))
                elif isinstance(ann, dm_Ellipse):
                    dataset_item_definition.append(("ellipse", label_idx))
                elif isinstance(ann, dm_Mask):
                    dataset_item_definition.append(("mask", label_idx))

        dataset_definition[str(item.id)] = dataset_item_definition

    return dataset_definition


def convert_dataset_definition_for_cross_project(
    dm_dataset_definition: DatasetDefinition,
    project_type_from: GetiProjectType,
    project_type_to: GetiProjectType,
) -> DatasetDefinition:
    """
    Convert annotation types in dm_dataset_definition for cross_project.

    :param dm_dataset_definition: Datumaro dataset definition keeping item information with annotation
    :param project_type_from: Source geti project type to be converted
    :param project_type_to: Target geti project type
    :return: converted datumaro dataset definition
    """
    SUPPORTED_CONVERSION = {
        (GetiProjectType.DETECTION, GetiProjectType.ROTATED_DETECTION): (
            ["bbox"],
            "polygon",
        ),
        (GetiProjectType.DETECTION, GetiProjectType.CLASSIFICATION): (
            ["bbox"],
            "label",
        ),
        (GetiProjectType.ROTATED_DETECTION, GetiProjectType.DETECTION): (
            ["polygon"],
            "bbox",
        ),
        (GetiProjectType.SEGMENTATION, GetiProjectType.DETECTION): (
            ["polygon", "ellipse", "mask"],
            "bbox",
        ),
        (GetiProjectType.ANOMALY_SEGMENTATION, GetiProjectType.ANOMALY_DETECTION): (
            ["polygon", "ellipse", "mask"],
            "bbox",
        ),
    }
    if project_type_from == GetiProjectType.INSTANCE_SEGMENTATION:
        project_type_from = GetiProjectType.SEGMENTATION
    mapping = (project_type_from, project_type_to)

    if mapping in SUPPORTED_CONVERSION:
        src_types, dst_type = SUPPORTED_CONVERSION[mapping]
        out_dataset_definition: DatasetDefinition = {}
        for key, val in dm_dataset_definition.items():
            anns: AnnotationDefinition = []
            for ann in val:
                if ann[0] in src_types:
                    anns.append((dst_type, ann[1]))
                else:
                    anns.append(ann)
            out_dataset_definition[key] = anns
        return out_dataset_definition

    return dm_dataset_definition


def get_sc_dataset_definition(  # noqa: C901
    annotation_scenes: list[AnnotationScene],
    label_names: list[str],
    label_map: dict[ID, Label],
) -> DatasetDefinition:
    """
    Convert list of SC annotation scenes to a dataset definition of the SC dataset.
    For examples of dataset definitions, see dataset definition fixtures
    :param annotation_scenes: list of the annotation scenes
    :param label_names: list of label names in the SC dataset
    :return: dataset definition representing SC annotation scenes
    """
    dataset_definition = {}
    for ann_scene in annotation_scenes:
        dataset_item_definition: AnnotationDefinition = []
        vis_map: dict[int, int] = {}
        for annotation in ann_scene.annotations:
            shape = annotation.shape
            ann_labels = [label_map[label.id_].name for label in annotation.get_labels()]
            for label in ann_labels:
                try:
                    label_idx = label_names.index(label)
                except ValueError:
                    pass  # skip
                if isinstance(shape, Rectangle) and Rectangle.is_full_box(shape):
                    dataset_item_definition.append(("label", label_idx))
                elif isinstance(shape, Rectangle):
                    dataset_item_definition.append(("bbox", label_idx))
                elif isinstance(shape, Polygon):
                    dataset_item_definition.append(("polygon", label_idx))
                elif isinstance(shape, Ellipse):
                    dataset_item_definition.append(("ellipse", label_idx))
                elif isinstance(shape, Keypoint):
                    vis_map[label_idx] = 2 if shape.is_visible else 1
        if vis_map:
            visibilities = [0] * len(label_names)
            for i, visibility in vis_map.items():
                visibilities[i] = visibility
            dataset_item_definition.append(("points", tuple(visibilities)))
        dataset_definition[str(ann_scene.id_)] = dataset_item_definition
    return dataset_definition


def check_thumbnails(project_id: ID, images: list[Image], videos: list[Video] = []) -> None:
    """
    Check if thumbnails exist in the ThumbnailBinaryRepo for given project and workspace

    :param project_id: project id
    :param images: list of images in the SC project
    """
    project = ProjectRepo().get_by_id(project_id)
    dataset_storage = project.get_training_dataset_storage()
    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=project.workspace_id,
        project_id=project_id,
        dataset_storage_id=dataset_storage.id_,
    )
    thumbnail_repo = ThumbnailBinaryRepo(dataset_storage_identifier)
    for image in images:
        thumbnail_name = f"{image.id_}_thumbnail.jpg"
        assert thumbnail_repo.exists(thumbnail_name)
    for video in videos:
        thumbnail_name = f"{video.id_}_thumbnail.jpg"
        assert thumbnail_repo.exists(thumbnail_name)


def check_dataset_items(  # noqa: C901
    project_id: ID,
    project_type: GetiProjectType,
    dm_dataset_definition: DatasetDefinition,
    annotation_scenes: list[AnnotationScene],
    all_labels: list[str],
    labels_to_keep: list[str],
    exact_same: bool = False,
):
    """
    Compare annotation items in sc project and dm_dataset_definition
    :param project_type: Geti Project Type
    :param dm_dataset_definition: Datumaro dataset definition keeping item information with annotation
    :param annotation_scenes: list of SC annotation scenes
    :param all_labels: all label names
    :param labels_to_keep: label names to keep in sc project
    :param exact_same: It True, all items in annotation_scenes and dm_dataset_definition must be identical.
                       Otherwise, some items in dm_dataset_definition may not exist in annotation_scenes.
    """
    project = ProjectRepo().get_by_id(project_id)
    project_labels = get_project_labels(project=project, include_empty=True)
    label_map = {label.id_: label for label in project_labels}
    sc_dataset_definition = get_sc_dataset_definition(annotation_scenes, all_labels, label_map)
    sc_items = [sorted(sc_item) for sc_item in sc_dataset_definition.values()]

    dm_items = []
    # convert mask to polygon
    for anns in list(dm_dataset_definition.values()):
        converted_anns = []
        for ann_type, label in anns:
            if ann_type == "mask":
                ann_type = "polygon"
            converted_anns.append((ann_type, label))
        dm_items.append(converted_anns)

    # filter dm items to remove labels not kept when loading
    domain_to_valid_types = {
        domain.name.lower(): [ann_type.name for ann_type in ann_types]
        for domain, ann_types in SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES.items()
    }
    label_domain = ImportUtils.project_type_to_label_domain(project_type)
    domain_str = label_domain.name.lower()
    labels_to_keep_indices = [all_labels.index(label_name) for label_name in labels_to_keep]
    for idx, dm_item in enumerate(dm_items):
        new_dm_item: AnnotationDefinition = []
        for ann_type, label in dm_item:
            if ann_type not in domain_to_valid_types[domain_str] or (
                ann_type != "points" and label not in labels_to_keep_indices
            ):
                continue
            if ann_type == "points":
                assert isinstance(label, tuple)  # here, label is actually visiability.
                # TODO : bump up datumaro to 1.10.0 or higher and remove this
                version = pkg_resources.get_distribution("datumaro").version
                if pkg_resources.parse_version(version) < pkg_resources.parse_version("1.10.0rc1"):
                    converted_visibility = [2] * len(labels_to_keep)
                else:
                    # We need to convert the visiability to have only labels to keep
                    converted_visibility = [0] * len(labels_to_keep)
                    for i in labels_to_keep_indices:
                        converted_visibility[i] = label[i]
                new_dm_item.append(("points", tuple(converted_visibility)))
            else:
                new_dm_item.append((ann_type, label))
        dm_items[idx] = sorted(new_dm_item)

    if exact_same:
        # assert all SC item definitions are identical to a DM datumaro definition
        assert len(sc_items) == len(dm_items)

    for sc_item in sc_items:
        dm_items.remove(sc_item)


def save_dataset(
    file_repo: ImportDataRepo,
    dataset: dm_Dataset,
    fmt: str,
) -> ID:
    """
    Save datumaro dataset to given format

    :param file_repo: file repo used to save dataset to filesystem
    :param dataset: datumaro dataset to save
    :param fmt: format to save dataset to
    :return: metadata of the saved dataset
    """
    dataset_id: ID = SessionBasedRepo.generate_id()
    dataset_dir = file_repo.get_dataset_directory(dataset_id)
    if fmt == "voc":
        dataset.transform("polygons_to_masks")
    dataset.export(dataset_dir, fmt, save_media=True)
    make_archive(dataset_dir, "zip", dataset_dir)

    return dataset_id


def save_dataset_with_path(
    file_repo: ImportDataRepo,
    dataset_path: str,
) -> ID:
    """
    Save datumaro dataset to given format

    :param file_repo: file repo used to save dataset to filesystem
    :param dataset: datumaro dataset to save
    :param fmt: format to save dataset to
    :return: metadata of the saved dataset
    """
    dataset_id: ID = SessionBasedRepo.generate_id()
    dataset_dir = file_repo.get_dataset_directory(dataset_id)
    os.makedirs(dataset_dir, exist_ok=True)
    if os.path.isdir(dataset_path):
        copytree(dataset_path, dataset_dir)
        make_archive(dataset_dir, "zip", dataset_dir)
    else:
        dst_path = file_repo.get_zipped_file_local_path(dataset_id)
        copyfile(dataset_path, dst_path)
        with zipfile.ZipFile(dst_path, "r") as zip_ref:
            zip_ref.extractall(dataset_dir)
    return dataset_id


def build_dataset_from_dataset_storage(
    dataset_storage: DatasetStorage, save_video_as_images: bool
) -> list[ScDatasetItem]:
    annotation_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)

    image_repo = ImageRepo(dataset_storage.identifier)
    video_repo = VideoRepo(dataset_storage.identifier)
    images_dict = {image.id_: image for image in image_repo.get_all()}
    videos_dict = {video.id_: video for video in video_repo.get_all()}

    media_identifiers: list[MediaIdentifierEntity] = []
    media_identifiers.extend(image_repo.get_all_identifiers())
    for video_id in videos_dict:
        annotated_frame_identifiers = annotation_scene_repo.get_annotated_video_frame_identifiers_by_video_id(
            video_id=video_id, annotation_kind=AnnotationSceneKind.ANNOTATION
        )
        if annotated_frame_identifiers:
            media_identifiers.extend(annotated_frame_identifiers)
        elif not save_video_as_images:
            media_identifiers.append(VideoIdentifier(video_id=video_id))

    # name_mapper = MediaNameIDMapper()
    items: list[ScDatasetItem] = []
    for media_identifier in media_identifiers:
        scene = annotation_scene_repo.get_latest_annotations_by_kind_and_identifiers(
            media_identifiers=[media_identifier],
            annotation_kind=AnnotationSceneKind.ANNOTATION,
        )[0]
        if isinstance(media_identifier, ImageIdentifier):
            media = images_dict[media_identifier.media_id]
        elif isinstance(media_identifier, VideoFrameIdentifier):
            video = videos_dict[media_identifier.media_id]
            media = VideoFrame(video=video, frame_index=media_identifier.frame_index)
        elif isinstance(media_identifier, VideoIdentifier):
            media = videos_dict[media_identifier.media_id]
        else:
            raise ValueError(f"Unexpected media '{media_identifier}' to export.")

        items.append(ScDatasetItem(media=media, annotation_scene=scene, id_=DatasetRepo.generate_id()))

    return items


class VideoAnnotationRangeKey(NamedTuple):
    video_path: str
    start_frame: int
    end_frame: int


class VideoAnnotationRangeValue(NamedTuple):
    label_indice: set[int]
    has_empty_label: bool


def get_video_annotation_range(
    dataset_storage: DatasetStorage,
    label_names: list[str] | None = None,
) -> dict[VideoAnnotationRangeKey, VideoAnnotationRangeValue]:
    video_repo = VideoRepo(dataset_storage.identifier)
    videos_dict = {video.id_: video for video in video_repo.get_all()}

    range_repo = VideoAnnotationRangeRepo(dataset_storage.identifier)
    ranges_dict = {}

    range_identifiers: list[RangeIdentifier] = []
    for ann_range in range_repo.get_all():
        if ann_range.video_id in videos_dict:
            ranges_dict[ann_range.id_] = ann_range
            identifiers = [RangeIdentifier(ann_range.id_, i) for i in range(len(ann_range.range_labels))]
            range_identifiers.extend(identifiers)

    project_identifier = ProjectIdentifier(
        workspace_id=dataset_storage.workspace_id, project_id=dataset_storage.project_id
    )
    label_schema = LabelSchemaRepo(project_identifier).get_latest()
    sc_labels = label_schema.get_labels(include_empty=False)
    if not label_names:
        label_map = {sc_label.id_: i for i, sc_label in enumerate(sc_labels)}
    else:
        label_map = {sc_label.id_: label_names.index(sc_label.name) for i, sc_label in enumerate(sc_labels)}

    video_mapper = VideoNameIDMapper()
    items = {}
    for identifier in range_identifiers:
        ann_range = ranges_dict[identifier.range_id]
        range_labels: RangeLabels = ann_range.range_labels[identifier.range_idx]

        video = videos_dict[ann_range.video_id]

        video_name = video_mapper.forward(video)
        extension = os.path.splitext(video.data_binary_filename)[1]
        video_path = f"{video_name}{extension}"

        has_empty_label = False
        label_indice = set()
        for label_id in range_labels.label_ids:
            try:
                label_indice.add(label_map[label_id])
            except KeyError:  # empty label
                has_empty_label = True

        key = VideoAnnotationRangeKey(video_path, range_labels.start_frame, range_labels.end_frame)
        value = VideoAnnotationRangeValue(label_indice, has_empty_label)
        assert key not in items
        items[key] = value

    return items


def check_video_annotation_ranges(
    dm_dataset: dm_Dataset,
    dataset_storage: DatasetStorage,
    label_names: list[str] | None = None,
    exact_match: bool = True,
    restored: bool = True,
) -> None:
    """
    Check if Videos are mapped to VideoAnnotationRange items.
    """
    sc_items = get_video_annotation_range(dataset_storage, label_names)

    dm_items: dict[VideoAnnotationRangeKey, VideoAnnotationRangeValue] = {}
    for item in dm_dataset:
        if restored and isinstance(item.media, dm_Video) and not ImportUtils.is_video_unannotated(item):
            # video annotation range is exported as Video media
            start_frame = item.media._start_frame
            end_frame = item.media._end_frame or 0
        elif not restored and isinstance(item.media, dm_VideoFrame):
            # video annotation range is created from VideoFrame media
            # This is for Classification task only.
            start_frame = item.media.index
            end_frame = item.media.index
        else:
            continue

        key = VideoAnnotationRangeKey(
            os.path.basename(item.media.path),
            start_frame,
            end_frame,
        )
        value = VideoAnnotationRangeValue(
            {int(ann.label) for ann in item.annotations},
            item.attributes.get("has_empty_label", False),
        )
        assert key not in dm_items
        dm_items[key] = value

    for dm_key, dm_value in dm_items.items():
        sc_value = sc_items.pop(dm_key)
        assert sc_value == dm_value

    if exact_match:
        assert len(sc_items) == 0


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
