# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import pytest
from sc_sdk.entities.video import VideoFrame
from sc_sdk.repos import ImageRepo, VideoRepo

from media_utils import get_image_bytes, get_image_numpy, get_video_bytes, get_video_frame_numpy
from tests.test_helpers import generate_random_annotated_project


@pytest.mark.ScSdkComponent
class TestMediaUtils:
    def test_get_image_bytes(self, request) -> None:
        project = generate_random_annotated_project(
            request,
            "__Test media utils",
            "",
            "detection",
            number_of_images=1,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        image_repo = ImageRepo(dataset_storage_identifier=dataset_storage.identifier)
        image = image_repo.get_one()
        assert image is not None

        data = get_image_bytes(dataset_storage_identifier=dataset_storage.identifier, image=image)

        assert len(data) == image.size

    def test_get_video_bytes(self, request) -> None:
        project = generate_random_annotated_project(
            request,
            "__Test media utils",
            "",
            "detection",
            number_of_images=0,
            number_of_videos=1,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        video_repo = VideoRepo(dataset_storage_identifier=dataset_storage.identifier)
        video = video_repo.get_one()
        assert video is not None

        data = get_video_bytes(dataset_storage_identifier=dataset_storage.identifier, video=video)

        assert len(data) == video.size

    def test_get_image_numpy(self, request) -> None:
        project = generate_random_annotated_project(
            request,
            "__Test media utils",
            "",
            "detection",
            number_of_images=1,
            number_of_videos=0,
            image_width=512,
            image_height=384,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        image_repo = ImageRepo(dataset_storage_identifier=dataset_storage.identifier)
        image = image_repo.get_one()
        assert image is not None

        numpy_data = get_image_numpy(dataset_storage_identifier=dataset_storage.identifier, image=image)

        assert numpy_data.shape == (384, 512, 3)

    def test_get_video_frame_numpy(self, request) -> None:
        project = generate_random_annotated_project(
            request,
            "__Test media utils",
            "",
            "detection",
            number_of_images=0,
            number_of_videos=1,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        video_repo = VideoRepo(dataset_storage_identifier=dataset_storage.identifier)
        video = video_repo.get_one()
        assert video is not None

        numpy_data = get_video_frame_numpy(
            dataset_storage_identifier=dataset_storage.identifier, video_frame=VideoFrame(video=video, frame_index=0)
        )

        assert numpy_data.shape == (360, 480, 3)
