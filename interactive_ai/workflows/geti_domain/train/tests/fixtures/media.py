# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import pytest
from geti_types import ID, ImageIdentifier
from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.video import Video, VideoFrame


@pytest.fixture
def fxt_image_identifier(fxt_mongo_id):
    yield ImageIdentifier(image_id=ID(fxt_mongo_id(0)))


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
def fxt_video_frame_entity_factory(fxt_ote_id):
    def _build_video_frame(
        index: int = 1,  # Frame index
        video_id_index: int = 1,
        video_name: str = "dummy video",
    ):
        video = Video(
            name=video_name,
            id=fxt_ote_id(video_id_index),
            uploader_id="",
            fps=30,
            height=32,
            width=32,
            total_frames=100,
            size=1000,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        return VideoFrame(
            video=video,
            frame_index=index,
        )

    yield _build_video_frame
