# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime
import io
import os
import tempfile

import cv2
import numpy as np
import pytest
from _pytest.fixtures import FixtureRequest
from tests.fixtures.values import DummyValues

from geti_types import ID, ImageIdentifier, MediaIdentifierEntity, VideoFrameIdentifier, VideoIdentifier
from iai_core.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core.entities.annotation_scene_state import AnnotationState
from iai_core.entities.datasets import DatasetIdentifier
from iai_core.entities.image import Image
from iai_core.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.project import Project
from iai_core.entities.video import Video, VideoExtensions
from iai_core.repos import VideoRepo
from media_utils import VideoInformation


@pytest.fixture
def fxt_annotation_scene_prediction(
    fxt_ote_id,
    fxt_image_identifier,
    fxt_rectangle_annotation,
):
    yield AnnotationScene(
        kind=AnnotationSceneKind.PREDICTION,
        media_identifier=fxt_image_identifier,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_ote_id(),
        creation_date=DummyValues.MODIFICATION_DATE_1,
        annotations=[
            fxt_rectangle_annotation,
        ],
    )


@pytest.fixture
def fxt_ote_id(fxt_mongo_id):
    """
    Create a realistic OTE ID for testing purposes. Based on the fxt_mongo_id, but this
    fixture returns an actual ID entity instead of a string.
    """

    def _build_ote_id(offset: int = 0) -> ID:
        return ID(fxt_mongo_id(offset))

    yield _build_ote_id


@pytest.fixture
def fxt_image_identifier_factory(fxt_mongo_id):
    def _build_image_identifier(index: int) -> ImageIdentifier:
        return ImageIdentifier(image_id=ID(fxt_mongo_id(index)))

    yield _build_image_identifier


@pytest.fixture
def fxt_image_identifier_1(fxt_image_identifier_factory):
    yield fxt_image_identifier_factory(0)


@pytest.fixture
def fxt_image_identifier_2(fxt_mongo_id):
    yield fxt_image_identifier_factory(1)


@pytest.fixture
def fxt_image_identifier(fxt_image_identifier_1):
    yield fxt_image_identifier_1


@pytest.fixture
def fxt_image_identifier_rest(fxt_mongo_id, fxt_image_identifier_1):
    yield {
        "type": fxt_image_identifier_1.media_type.value,
        "image_id": fxt_mongo_id(),
    }


@pytest.fixture
def fxt_video_identifier(fxt_mongo_id):
    yield VideoIdentifier(video_id=ID(fxt_mongo_id()))


@pytest.fixture
def fxt_video_identifier_rest(fxt_mongo_id, fxt_video_identifier):
    yield {
        "type": fxt_video_identifier.media_type.value,
        "video_id": fxt_mongo_id(),
    }


@pytest.fixture
def fxt_video_frame_identifier(fxt_mongo_id):
    yield VideoFrameIdentifier(video_id=ID(fxt_mongo_id()), frame_index=DummyValues.FRAME_INDEX)


@pytest.fixture
def fxt_video_frame_identifier_rest(fxt_mongo_id, fxt_video_frame_identifier):
    yield {
        "type": fxt_video_frame_identifier.media_type.value,
        "video_id": fxt_mongo_id(),
        "frame_index": DummyValues.FRAME_INDEX,
    }


@pytest.fixture
def fxt_media_identifier_factory(fxt_image_identifier_factory):
    def _build_media_identifier(index: int) -> MediaIdentifierEntity:
        return fxt_image_identifier_factory(index)

    yield _build_media_identifier


@pytest.fixture
def fxt_media_identifier_1(fxt_media_identifier_factory):
    yield fxt_media_identifier_factory(0)


@pytest.fixture
def fxt_media_identifier_2(fxt_media_identifier_factory):
    yield fxt_media_identifier_factory(1)


@pytest.fixture
def fxt_media_identifier(fxt_media_identifier_1):
    yield fxt_media_identifier_1


@pytest.fixture
def fxt_media_identifier_rest(fxt_image_identifier_rest):
    yield fxt_image_identifier_rest


@pytest.fixture
def fxt_solid_color_image_bytes():
    """Create an image (as bytes) with custom height, width, extension and color."""

    def _build_image(height: int = 50, width: int = 100, extension: str = "jpg", fill_value: int = 0) -> bytes:
        image_shape = (height, width, 3)
        _, blank_image = cv2.imencode(f".{extension}", np.full(image_shape, fill_value, dtype=np.uint8))
        return io.BytesIO(blank_image).read()  # type: ignore

    yield _build_image


@pytest.fixture
def fxt_image_entity_factory(fxt_ote_id, fxt_dataset_storage):
    def _build_image(index: int = 1, name: str = "dummy image"):
        return Image(
            name=name,
            uploader_id="",
            id=fxt_ote_id(index),
            height=32,
            width=32,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )

    yield _build_image


@pytest.fixture
def fxt_image_entity(fxt_image_entity_factory):
    yield fxt_image_entity_factory(1)


@pytest.fixture
def fxt_video_information():
    yield VideoInformation(fps=10, height=10, width=10, total_frames=100)


@pytest.fixture
def fxt_dataset_identifier(fxt_dataset_storage, fxt_dataset):
    yield DatasetIdentifier.from_ds_identifier(
        dataset_storage_identifier=fxt_dataset_storage.identifier,
        dataset_id=fxt_dataset.id_,
    )


@pytest.fixture
def fxt_media_numpy():
    yield np.ones((100, 100, 3), dtype=np.float32)


@pytest.fixture
def fxt_media_entities_list(fxt_image_entity, fxt_video_entity):
    yield [fxt_image_entity, fxt_video_entity]


@pytest.fixture
def fxt_media_states_per_task(fxt_image_entity, fxt_video_entity, fxt_mongo_id):
    yield {
        fxt_image_entity.media_identifier: {fxt_mongo_id(0): AnnotationState.ANNOTATED},
        fxt_video_entity.media_identifier: {fxt_mongo_id(1): AnnotationState.ANNOTATED},
    }


@pytest.fixture
def fxt_unannotated_video_factory(
    request: FixtureRequest,
    fxt_image_entity_factory,
    fxt_ote_id,
    fxt_numpy_image_factory,
):
    """
    This is a fixture to create and save a random video with annotations. Both video
    and annotations are stored in their respective repositories, and removed after
    the test.

    The factory generates shapes that are either 'rectangle', 'ellipse' or 'triangle'
    on a white background. The shapes to be generated are deduced from the labels
    in the project. If the project labels do not match the shape names, all three
    sorts of random shapes are generated.
    """

    def _video_factory(
        project: Project,
        width: int = 480,
        height: int = 360,
        number_of_frames: int = 150,
    ) -> Video:
        """
        generate a video that is 150 frames at 30 fps by default. Video contains random
        shapes on white background

        :param project: Project that the Video will added to
        :param width: Width of the video
        :param height: Height of the video
        :param number_of_frames: Amount of frames to generate
        :return: Tuple(Video entity, list of AnnotationScene entities)
        """

        dataset_storage = project.get_training_dataset_storage()
        # Generate video
        video_repo: VideoRepo = VideoRepo(dataset_storage.identifier)
        # Generate a video path
        video_id = video_repo.generate_id()
        video_path = os.path.join(tempfile.gettempdir(), f"{video_id}.mp4")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
        fps = 30.0
        video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

        # Generate frames
        for _i in range(number_of_frames):
            image, _ = fxt_numpy_image_factory(image_width=width, image_height=height)

            video_writer.write(image=image)
        video_writer.release()

        filename = video_repo.binary_repo.save(data_source=video_path, dst_file_name=video_path)
        size = video_repo.binary_repo.get_object_size(filename)
        request.addfinalizer(lambda: video_repo.binary_repo.delete_by_filename(filename=filename))

        # Remove input binary after save
        if os.path.exists(video_path):
            os.remove(video_path)

        _, extension = os.path.splitext(filename)
        try:
            video_extension = VideoExtensions[extension[1:].upper()]
        except KeyError:
            video_extension = VideoExtensions.MP4

        video = Video(
            name="Generated video",
            stride=1,
            creation_date=DummyValues.CREATION_DATE,
            id=video_id,
            uploader_id="",
            extension=video_extension,
            fps=fps,
            width=width,
            height=height,
            total_frames=number_of_frames,
            size=size,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        video_repo.save(video)
        request.addfinalizer(lambda: video_repo.delete_by_id(video.id_))

        return video

    return _video_factory


@pytest.fixture
def fxt_image(fxt_ote_id) -> Image:
    return Image(
        name="dummy_image.jpg",
        uploader_id=DummyValues.CREATOR_NAME,
        id=fxt_ote_id(1),
        creation_date=datetime.datetime(
            year=2023,
            month=9,
            day=8,
            hour=1,
            minute=5,
            second=12,
            tzinfo=datetime.timezone.utc,
        ),
        width=100,
        height=100,
        size=100,
        extension=ImageExtensions.JPG,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )
