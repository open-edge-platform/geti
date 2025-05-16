# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import io
import os
from unittest.mock import ANY, MagicMock, call, patch

import numpy as np
import pytest

from communication.exceptions import (
    FileNotFoundException,
    ImageNotFoundException,
    MediaNotPreprocessedException,
    ProjectLockedException,
    VideoFrameNotFoundException,
    VideoFrameOutOfRangeException,
    VideoNotFoundException,
    VideoThumbnailNotFoundException,
)
from communication.rest_views.filtered_dataset_rest_views import FilteredDatasetRESTView
from resource_management.media_manager import IMAGE_EXT_SAVE_MAPPING, MediaManager
from usecases.dataset_filter import DatasetFilter
from usecases.query_builder import MediaQueryResult, QueryResults

from geti_fastapi_tools.exceptions import InvalidMediaException
from geti_kafka_tools import publish_event
from geti_types import ID
from iai_core.adapters.binary_interpreters import RAWBinaryInterpreter
from iai_core.entities.image import Image, NullImage
from iai_core.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from iai_core.entities.video import NullVideo, Video, VideoFrame
from iai_core.repos import ImageRepo, ProjectRepo, VideoRepo
from iai_core.repos.storage.binary_repos import ThumbnailBinaryRepo, VideoBinaryRepo
from iai_core.repos.storage.storage_client import BytesStream
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.media_factory import Media2DFactory
from media_utils import VideoFileRepair, VideoFrameOutOfRangeInternalException, VideoFrameReader, VideoFrameReadingError
from media_utils.video_decoder import _VideoDecoderOpenCV


class TestMediaManager:
    def test_image_extension_mapping(self) -> None:
        """Ensure that every image format is mapped to some extension for saving."""
        for ext in ImageExtensions:
            assert ext in IMAGE_EXT_SAVE_MAPPING, f"Extension {ext} is not mapped"

    @pytest.mark.parametrize("only_preprocessed", [True, False])
    def test_get_first_media_image(self, request, fxt_image_entity, fxt_dataset_storage, only_preprocessed) -> None:
        ds_identifier = fxt_dataset_storage.identifier
        image = fxt_image_entity
        with (
            patch.object(ImageRepo, "get_one", return_value=image) as mock_get_one_image,
            patch.object(VideoRepo, "get_one", return_value=NullVideo()) as mock_get_one_video,
        ):
            found_media = MediaManager.get_first_media(ds_identifier, only_preprocessed)

        mock_get_one_image.assert_called_once_with(
            earliest=True, extra_filter=None if not only_preprocessed else {"preprocessed": {"status": "FINISHED"}}
        )
        mock_get_one_video.assert_not_called()
        assert found_media == image

    @pytest.mark.parametrize("only_preprocessed", [True, False])
    def test_get_first_media_video(self, request, fxt_video_entity, fxt_dataset_storage, only_preprocessed) -> None:
        ds_identifier = fxt_dataset_storage.identifier
        extra_filter = None if not only_preprocessed else {"preprocessed": {"status": "FINISHED"}}
        with (
            patch.object(ImageRepo, "get_one", return_value=NullImage()) as mock_get_one_image,
            patch.object(VideoRepo, "get_one", return_value=fxt_video_entity) as mock_get_one_video,
        ):
            found_media = MediaManager.get_first_media(ds_identifier, only_preprocessed)

        mock_get_one_image.assert_called_once_with(earliest=True, extra_filter=extra_filter)
        mock_get_one_video.assert_called_once_with(earliest=True, extra_filter=extra_filter)
        assert found_media == fxt_video_entity

    @pytest.mark.parametrize("only_preprocessed", [True, False])
    def test_get_first_media_none(self, request, fxt_dataset_storage, only_preprocessed) -> None:
        ds_identifier = fxt_dataset_storage.identifier
        extra_filter = None if not only_preprocessed else {"preprocessed": {"status": "FINISHED"}}
        with (
            patch.object(ImageRepo, "get_one", return_value=NullImage()) as mock_get_one_image,
            patch.object(VideoRepo, "get_one", return_value=NullVideo()) as mock_get_one_video,
        ):
            found_media = MediaManager.get_first_media(ds_identifier, only_preprocessed)

        mock_get_one_image.assert_called_once_with(earliest=True, extra_filter=extra_filter)
        mock_get_one_video.assert_called_once_with(earliest=True, extra_filter=extra_filter)
        assert found_media is None

    def test_upload_image(
        self,
        fxt_solid_color_image_bytes,
        fxt_dataset_storage_identifier,
        fxt_mongo_id,
    ) -> None:
        image_bytes = fxt_solid_color_image_bytes(height=50, width=50)
        with (
            patch.object(MediaManager, "validate_image_dimensions") as mock_validate_dims,
            patch.object(ImageRepo, "save") as mock_save_image,
            patch.object(Media2DFactory, "create_and_save_media_thumbnail") as mock_create_and_save_thumbnail,
        ):
            image = MediaManager.upload_image(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                basename="test_image",
                extension=ImageExtensions.JPG,
                data_stream=BytesStream(data=io.BytesIO(image_bytes), length=len(image_bytes)),
                user_id=ID("dummy_user"),
                update_metrics=True,
            )

        mock_validate_dims.assert_called_once()
        assert mock_save_image.call_count == 2
        mock_save_image.assert_has_calls(
            [
                call(
                    Image(
                        name="test_image",
                        uploader_id="dummy_user",
                        id=ANY,
                        extension=ImageExtensions.JPG,
                        width=50,
                        height=50,
                        size=ANY,
                        preprocessing=MediaPreprocessing(
                            status=MediaPreprocessingStatus.IN_PROGRESS,
                            start_timestamp=ANY,
                        ),
                    )
                ),
                call(
                    Image(
                        name="test_image",
                        uploader_id="dummy_user",
                        id=ANY,
                        extension=ImageExtensions.JPG,
                        width=50,
                        height=50,
                        size=ANY,
                        preprocessing=MediaPreprocessing(
                            status=MediaPreprocessingStatus.FINISHED,
                            start_timestamp=ANY,
                            end_timestamp=ANY,
                        ),
                    )
                ),
            ]
        )
        mock_create_and_save_thumbnail.assert_called_once()

        assert isinstance(image, Image)
        assert image.width == 50 and image.height == 50

    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_upload_image_async_preprocessing(
        self,
        fxt_solid_color_image_bytes,
        fxt_dataset_storage_identifier,
    ) -> None:
        image_bytes = fxt_solid_color_image_bytes(height=50, width=50)
        with (
            patch.object(MediaManager, "validate_image_dimensions") as mock_validate_dims,
            patch.object(ImageRepo, "save") as mock_save_image,
            patch("resource_management.media_manager.publish_event") as mock_publish_event,
        ):
            image = MediaManager.upload_image(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                basename="test_image",
                extension=ImageExtensions.JPG,
                data_stream=BytesStream(data=io.BytesIO(image_bytes), length=len(image_bytes)),
                user_id=ID("dummy_user"),
                update_metrics=True,
            )

        mock_validate_dims.assert_called_once()
        mock_save_image.assert_called_once_with(
            Image(
                name="test_image",
                uploader_id="dummy_user",
                id=ANY,
                extension=ImageExtensions.JPG,
                width=50,
                height=50,
                size=ANY,
                preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.SCHEDULED, start_timestamp=ANY),
            )
        )
        mock_publish_event.assert_called_once_with(
            topic="media_preprocessing",
            body={
                "workspace_id": str(fxt_dataset_storage_identifier.workspace_id),
                "project_id": str(fxt_dataset_storage_identifier.project_id),
                "dataset_storage_id": str(fxt_dataset_storage_identifier.dataset_storage_id),
                "media_id": str(image.id_),
                "data_binary_filename": image.data_binary_filename,
                "media_type": "IMAGE",
                "event": "MEDIA_UPLOADED",
            },
            key=str(image.id_).encode(),
            headers_getter=ANY,
        )

        assert isinstance(image, Image)
        assert image.width == 50 and image.height == 50

    @patch("resource_management.media_manager.MAX_NUMBER_OF_PIXELS", 7680 * 4620)
    @pytest.mark.parametrize(
        "img_width, img_height",
        [(31, 31), (20001, 32), (32, 20001), (0, 0), (7681, 4620)],
    )
    def test_upload_image_bad_dimensions(
        self,
        img_width,
        img_height,
        fxt_solid_color_image_bytes,
        fxt_dataset_storage_identifier,
    ) -> None:
        if (img_width, img_height) == (0, 0):
            test_image = bytes(0)
        else:
            test_image = fxt_solid_color_image_bytes(width=img_width, height=img_height)
        with (
            patch.object(ImageRepo, "save") as mock_save,
            pytest.raises(InvalidMediaException),
        ):
            MediaManager().upload_image(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                basename="test_image",
                extension=ImageExtensions.JPG,
                data_stream=BytesStream(data=io.BytesIO(test_image), length=len(test_image)),
                user_id=ID("dummy_user"),
            )

            mock_save.assert_called()

    def test_upload_video(
        self,
        fxt_project,
        request,
        fxt_unannotated_video_factory,
    ) -> None:
        project = fxt_project
        dataset_storage = project.get_training_dataset_storage()
        height, width, number_of_frames = 360, 480, 1
        video_binary_repo = VideoBinaryRepo(project.get_training_dataset_storage().identifier)
        video = fxt_unannotated_video_factory(
            project=project,
            height=height,
            width=width,
            number_of_frames=number_of_frames,
        )

        video_data = video_binary_repo.get_by_filename(
            filename=video.data_binary_filename,
            binary_interpreter=RAWBinaryInterpreter(),
        )
        with patch.object(VideoRepo, "save") as mock_video_save:
            # Temporarily save the video bytes to the BinaryRepo and use this URL
            # as mock url when the BinaryRepo is called
            temp_filename = video_binary_repo.save(
                dst_file_name="file.mp4",
                data_source=video_data,
            )
            request.addfinalizer(lambda: video_binary_repo.delete_by_filename(filename=temp_filename))
            with (
                patch.object(VideoBinaryRepo, "save", return_value=temp_filename) as mock_save_video,
                patch.object(
                    MediaManager,
                    "get_video_frame_thumbnail_numpy",
                    return_value=np.array([]),
                ) as mock_get_thumbnail_numpy,
                patch.object(VideoRepo, "generate_id", return_value="sample_id"),
                patch.object(Media2DFactory, "create_and_save_media_thumbnail") as mock_create_thumbnail,
            ):
                video = MediaManager.upload_video(
                    dataset_storage_identifier=dataset_storage.identifier,
                    basename="file",
                    extension=VideoExtensions.MP4,
                    data_stream=BytesStream(data=io.BytesIO(video_data), length=len(video_data)),
                    user_id=ID("dummy_user"),
                    update_metrics=True,
                )

        mock_save_video.assert_called_once_with(dst_file_name="sample_id.mp4", data_source=ANY)
        mock_get_thumbnail_numpy.assert_called()
        mock_create_thumbnail.assert_called()
        assert mock_video_save.call_count == 2
        mock_video_save.assert_has_calls(
            [
                call(
                    Video(
                        id=ANY,
                        name="file",
                        extension=VideoExtensions.MP4,
                        uploader_id="dummy_user",
                        fps=30,
                        width=width,
                        height=height,
                        total_frames=number_of_frames,
                        size=ANY,
                        preprocessing=MediaPreprocessing(
                            status=MediaPreprocessingStatus.IN_PROGRESS,
                            start_timestamp=ANY,
                        ),
                    )
                ),
                call(
                    Video(
                        id=ANY,
                        name="file",
                        extension=VideoExtensions.MP4,
                        uploader_id="dummy_user",
                        fps=30,
                        width=width,
                        height=height,
                        total_frames=number_of_frames,
                        size=ANY,
                        preprocessing=MediaPreprocessing(
                            status=MediaPreprocessingStatus.FINISHED,
                            start_timestamp=ANY,
                            end_timestamp=ANY,
                        ),
                    )
                ),
            ]
        )
        assert isinstance(video, Video)
        assert video.height == height
        assert video.width == width
        assert video.total_frames == number_of_frames

    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_upload_video_async_preprocessing(
        self,
        fxt_project,
        fxt_mongo_id,
        fxt_label,
        request,
        fxt_random_annotated_video_factory,
    ) -> None:
        project = fxt_project
        dataset_storage = project.get_training_dataset_storage()
        height, width, number_of_frames = 360, 480, 1
        labels = [fxt_label]
        video_binary_repo = VideoBinaryRepo(project.get_training_dataset_storage().identifier)
        video, _, _, _, _, _, _ = fxt_random_annotated_video_factory(
            project=project,
            height=height,
            width=width,
            number_of_frames=number_of_frames,
            labels=labels,
        )

        video_data = video_binary_repo.get_by_filename(
            filename=video.data_binary_filename, binary_interpreter=RAWBinaryInterpreter()
        )
        with patch.object(VideoRepo, "save") as mock_video_save:
            # Temporarily save the video bytes to the BinaryRepo and use this URL
            # as mock url when the BinaryRepo is called
            temp_filename = video_binary_repo.save(
                dst_file_name="file.mp4",
                data_source=video_data,
            )
            request.addfinalizer(lambda: video_binary_repo.delete_by_filename(filename=temp_filename))
            with (
                patch.object(VideoBinaryRepo, "save", return_value=temp_filename) as mock_save_video,
                patch.object(VideoRepo, "generate_id", return_value="sample_id"),
                patch("resource_management.media_manager.publish_event") as mock_publish_event,
            ):
                video = MediaManager.upload_video(
                    dataset_storage_identifier=dataset_storage.identifier,
                    basename="file",
                    extension=VideoExtensions.MP4,
                    data_stream=BytesStream(data=io.BytesIO(video_data), length=len(video_data)),
                    user_id=ID("dummy_user"),
                    update_metrics=True,
                )

        mock_save_video.assert_called_once_with(dst_file_name="sample_id.mp4", data_source=ANY)
        mock_video_save.assert_called_once_with(
            Video(
                id=ANY,
                name="file",
                extension=VideoExtensions.MP4,
                uploader_id="dummy_user",
                fps=30,
                width=width,
                height=height,
                total_frames=number_of_frames,
                size=ANY,
                preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.IN_PROGRESS, start_timestamp=ANY),
            )
        )
        mock_publish_event.assert_called_once_with(
            topic="media_preprocessing",
            body={
                "workspace_id": str(dataset_storage.identifier.workspace_id),
                "project_id": str(dataset_storage.identifier.project_id),
                "dataset_storage_id": str(dataset_storage.identifier.dataset_storage_id),
                "media_id": str(video.id_),
                "data_binary_filename": video.data_binary_filename,
                "media_type": "VIDEO",
                "event": "MEDIA_UPLOADED",
            },
            key=str(video.id_).encode(),
            headers_getter=ANY,
        )
        assert isinstance(video, Video)
        assert video.height == height
        assert video.width == width
        assert video.total_frames == number_of_frames

    @pytest.mark.parametrize("video_height, video_width, video_num_frames", [(5000, 480, 1), (30, 480, 1)])
    def test_upload_video_error(
        self,
        video_height,
        video_width,
        video_num_frames,
        fxt_project,
        fxt_unannotated_video_factory,
        request,
    ) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        video = fxt_unannotated_video_factory(
            project=fxt_project,
            height=video_height,
            width=video_width,
            number_of_frames=video_num_frames,
        )
        # Temporarily save the video bytes to the BinaryRepo and use this URL
        # as mock url when the BinaryRepo is called
        video_binary_repo = VideoBinaryRepo(dataset_storage.identifier)
        video_data = video_binary_repo.get_by_filename(
            filename=video.data_binary_filename,
            binary_interpreter=RAWBinaryInterpreter(),
        )
        temp_filename = video_binary_repo.save(
            dst_file_name="file.mp4",
            data_source=video_data,
        )
        request.addfinalizer(lambda: video_binary_repo.delete_by_filename(temp_filename))
        with (
            patch.object(VideoBinaryRepo, "save", return_value=temp_filename) as mock_save,
            pytest.raises(InvalidMediaException),
            patch.object(VideoBinaryRepo, "exists", return_value=True),
        ):
            MediaManager.upload_video(
                dataset_storage_identifier=dataset_storage.identifier,
                basename="file",
                extension=VideoExtensions.MP4,
                data_stream=BytesStream(data=io.BytesIO(video_data), length=len(video_data)),
                user_id=ID("dummy_user"),
            )

            mock_save.assert_called()

    def test_upload_video_too_long_error(
        self,
        fxt_project,
        fxt_unannotated_video_factory,
        request,
        fxt_video_information,
    ) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        video = fxt_unannotated_video_factory(
            project=fxt_project,
            height=50,
            width=50,
            number_of_frames=10,  # Mock this instead, since we don't want to create a huge video
        )
        # Temporarily save the video bytes to the BinaryRepo and use this URL
        # as mock url when the BinaryRepo is called
        video_binary_repo = VideoBinaryRepo(dataset_storage.identifier)
        video_data = video_binary_repo.get_by_filename(
            filename=video.data_binary_filename,
            binary_interpreter=RAWBinaryInterpreter(),
        )
        temp_filename = video_binary_repo.save(
            dst_file_name="file.mp4",
            data_source=video_data,
        )
        _video_decoder = _VideoDecoderOpenCV()  # type: ignore

        request.addfinalizer(lambda: video_binary_repo.delete_by_filename(filename=temp_filename))
        with (
            patch.object(VideoBinaryRepo, "save", return_value=temp_filename) as mock_save,
            patch.object(VideoBinaryRepo, "exists", return_value=True),
            patch.object(
                _video_decoder,
                "get_video_information",
                return_value=fxt_video_information,
            ),
            patch.object(VideoFileRepair, "check_and_repair_video", return_value=True),
            patch.object(Video, "duration", 1000000),
            pytest.raises(
                InvalidMediaException,
                match="Video too long: the maximum duration is 3 hours",
            ),
        ):
            MediaManager().upload_video(
                dataset_storage_identifier=dataset_storage.identifier,
                basename="file",
                extension=VideoExtensions.MP4,
                data_stream=BytesStream(data=io.BytesIO(video_data), length=len(video_data)),
                user_id=ID("user_id"),
            )

            mock_save.assert_called()

    def test_filtered_dataset_to_rest_video_frames(
        self,
        fxt_project,
        fxt_dataset_storage_identifier,
        fxt_video_frame_identifier,
        fxt_video_entity,
    ) -> None:
        mock_media_entities_data = [
            MediaQueryResult(media_identifier=fxt_video_frame_identifier, media=fxt_video_entity)
        ]
        query_results = QueryResults(
            media_query_results=mock_media_entities_data,
            skip=100,
            matching_images_count=100,
            matching_videos_count=100,
            matching_video_frames_count=100,
            total_images_count=0,
            total_videos_count=0,
        )
        mock_anno_states_per_task = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
            media_identifiers=query_results.media_identifiers,
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            project=fxt_project,
        )
        dataset_filter = DatasetFilter.from_dict(query={}, limit=100)
        results = FilteredDatasetRESTView.filtered_dataset_storage_to_rest(
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            dataset_filter=dataset_filter,
            query_results=query_results,
            media_annotation_states_per_task=mock_anno_states_per_task,
        )
        assert results["media"][0]["type"] == "video_frame"
        assert results["media"][0]["frame_index"] == fxt_video_frame_identifier.frame_index

    def test_get_image_by_id(self, mock_image_repo, fxt_dataset_storage, fxt_image_entity) -> None:
        # Arrange
        IMAGE_ID = ID("image_id_123")

        # Act
        with patch.object(ImageRepo, "get_by_id", return_value=fxt_image_entity) as mock_get_by_id:
            result = MediaManager.get_image_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                image_id=IMAGE_ID,
            )

        mock_get_by_id.assert_called_once_with(IMAGE_ID)
        assert result == fxt_image_entity

    def test_get_image_by_id_error(self, mock_image_repo, fxt_dataset_storage) -> None:
        # Arrange
        IMAGE_ID = ID("image_id_124")

        # Act
        with (
            patch.object(ImageRepo, "get_by_id", return_value=NullImage()),
            pytest.raises(ImageNotFoundException),
        ):
            MediaManager.get_image_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                image_id=IMAGE_ID,
            )

    def test_get_video_by_id(self, fxt_dataset_storage_identifier, fxt_video_entity) -> None:
        # Arrange
        VIDEO_ID = ID("video_id_123")

        # Act
        with (
            patch.object(VideoRepo, "__init__", lambda _self, _dataset_storage: None),
            patch.object(VideoRepo, "get_by_id", return_value=fxt_video_entity) as mock_get_by_id,
        ):
            result = MediaManager.get_video_by_id(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video_id=VIDEO_ID,
            )

        mock_get_by_id.assert_called_once_with(VIDEO_ID)
        assert result == fxt_video_entity

    def test_get_video_by_id_error(self, fxt_dataset_storage_identifier) -> None:
        # Arrange
        VIDEO_ID = ID("video_id_124")

        # Act
        with (
            patch.object(VideoRepo, "__init__", lambda _self, _dataset_storage: None),
            patch.object(VideoRepo, "get_by_id", return_value=NullVideo()),
            pytest.raises(VideoNotFoundException),
        ):
            MediaManager.get_video_by_id(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video_id=VIDEO_ID,
            )

    def test_validate_video_frame_exists(self, fxt_dataset_storage_identifier, fxt_video_entity, fxt_mongo_id) -> None:
        # Arrange
        VIDEO_ID = fxt_mongo_id(1)
        FRAME_INDEX = 5
        video = MagicMock()
        video.total_frames = 10

        # Act
        with patch.object(MediaManager, "get_video_by_id", return_value=video) as mock_get_video:
            result = MediaManager().validate_video_frame_exists(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video_id=VIDEO_ID,
                frame_index=FRAME_INDEX,
            )

        mock_get_video.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage_identifier, video_id=VIDEO_ID
        )
        assert result == video

    def test_validate_video_frame_exists_error(
        self, fxt_dataset_storage_identifier, fxt_video_entity, fxt_mongo_id
    ) -> None:
        # Arrange
        VIDEO_ID = fxt_mongo_id(1)
        FRAME_INDEX = 5
        video = MagicMock()
        video.total_frames = 5

        # Act
        with (
            patch.object(MediaManager, "get_video_by_id", return_value=video),
            pytest.raises(VideoFrameNotFoundException),
        ):
            MediaManager().validate_video_frame_exists(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video_id=VIDEO_ID,
                frame_index=FRAME_INDEX,
            )

    def test_get_video_frame_by_id(self, fxt_dataset_storage, fxt_video_entity, fxt_mongo_id) -> None:
        # Arrange
        VIDEO_ID = fxt_mongo_id(1)
        FRAME_INDEX = 5
        NPARRAY = np.array([0, 1, 2])
        video = MagicMock()
        video.total_frames = 10

        # Act
        with (
            patch.object(MediaManager, "get_video_by_id", return_value=video) as mock_get_video,
            patch(
                "resource_management.media_manager.get_media_roi_numpy",
                return_value=NPARRAY,
            ) as mock_get_media_roi_numpy,
        ):
            result = MediaManager.get_video_frame_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=VIDEO_ID,
                frame_index=FRAME_INDEX,
            )

        mock_get_video.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            video_id=VIDEO_ID,
        )
        mock_get_media_roi_numpy.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            media=VideoFrame(video=video, frame_index=FRAME_INDEX),
            roi_shape=None,
        )
        assert (result == NPARRAY).all()

    def test_get_video_frame_by_id_file_not_found(self, fxt_dataset_storage, fxt_video_entity) -> None:
        FRAME_INDEX = 5

        # Act
        with (
            patch.object(MediaManager, "get_video_by_id", return_value=fxt_video_entity) as mock_get_video,
            patch(
                "resource_management.media_manager.get_media_roi_numpy",
                side_effect=FileNotFoundError,
            ) as mock_get_media_roi_numpy,
            pytest.raises(FileNotFoundException),
        ):
            MediaManager.get_video_frame_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=fxt_video_entity.id_,
                frame_index=FRAME_INDEX,
            )

        mock_get_video.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            video_id=fxt_video_entity.id_,
        )
        mock_get_media_roi_numpy.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            media=VideoFrame(video=fxt_video_entity, frame_index=FRAME_INDEX),
            roi_shape=None,
        )

    def test_get_video_frame_by_id_no_index(self, fxt_dataset_storage, fxt_video_entity) -> None:
        # Arrange
        VIDEO_ID = ID("video_id_125")
        NPARRAY = np.array([3, 4, 5])
        video = MagicMock()
        video.total_frames = 6

        # Act
        with (
            patch.object(MediaManager, "get_video_by_id", return_value=video) as mock_get_video,
            patch(
                "resource_management.media_manager.get_media_roi_numpy",
                return_value=NPARRAY,
            ) as mock_get_media_roi_numpy,
        ):
            result = MediaManager.get_video_frame_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=VIDEO_ID,
            )

        mock_get_video.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage.identifier, video_id=VIDEO_ID
        )
        mock_get_media_roi_numpy.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            media=VideoFrame(video=video, frame_index=3),
            roi_shape=None,
        )
        assert (result == NPARRAY).all()

    def test_get_video_frame_by_id_out_of_range(self, fxt_dataset_storage, fxt_video_entity, fxt_mongo_id) -> None:
        # Arrange
        VIDEO_ID = fxt_mongo_id(1)
        FRAME_INDEX = 20
        video = MagicMock()
        video.total_frames = 10

        # Act
        with (
            patch.object(MediaManager, "get_video_by_id", return_value=video) as mock_get_video,
            patch.object(
                VideoFrameReader,
                "get_frame_numpy",
                side_effect=VideoFrameOutOfRangeInternalException,
            ) as mock_get_frame_numpy,
            pytest.raises(VideoFrameOutOfRangeException),
        ):
            MediaManager.get_video_frame_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=VIDEO_ID,
                frame_index=FRAME_INDEX,
            )

        # Assert
        mock_get_video.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            video_id=VIDEO_ID,
        )
        mock_get_frame_numpy.assert_called_once_with(file_location_getter=ANY, frame_index=FRAME_INDEX)

    def test_get_video_thumbnail_frame_by_id_out_of_range(
        self, fxt_dataset_storage, fxt_video_entity, fxt_mongo_id
    ) -> None:
        # Arrange
        VIDEO_ID = fxt_mongo_id(1)
        FRAME_INDEX = 20
        video = MagicMock()
        video.total_frames = 10

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video),
            patch.object(
                MediaManager,
                "get_single_thumbnail_frame_numpy",
                side_effect=VideoFrameOutOfRangeInternalException,
            ) as mock_get_single_thumbnail_frame_numpy,
            pytest.raises(VideoFrameOutOfRangeException),
        ):
            MediaManager.get_video_thumbnail_frame_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=VIDEO_ID,
                frame_index=FRAME_INDEX,
            )

        # Assert
        mock_get_single_thumbnail_frame_numpy.assert_called_once_with(
            video=video,
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            frame_index=FRAME_INDEX,
        )

    def test_get_video_thumbnail_frame_by_id_not_ready(
        self, fxt_dataset_storage, fxt_video_entity, fxt_mongo_id
    ) -> None:
        # Arrange
        video = MagicMock()
        video.total_frames = 10
        return_frame = [0, 0]

        video_frame = MagicMock()

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video),
            patch.object(
                MediaManager,
                "get_single_thumbnail_frame_numpy",
                side_effect=VideoFrameReadingError,
            ),
            patch.object(VideoFrameReader, "get_frame_numpy", return_value=video_frame),
            patch.object(Media2DFactory, "crop_to_thumbnail", return_value=return_frame),
        ):
            np_frame = MediaManager.get_video_thumbnail_frame_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=fxt_mongo_id(1),
                frame_index=1,
            )
        # Assert
        assert np_frame == return_frame

    @pytest.mark.parametrize(
        "preprocessing_status",
        [MediaPreprocessingStatus.SCHEDULED, MediaPreprocessingStatus.IN_PROGRESS, MediaPreprocessingStatus.FAILED],
    )
    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_get_video_thumbnail_frame_by_id_async_preprocessing_not_ready(
        self, fxt_dataset_storage, fxt_mongo_id, preprocessing_status
    ) -> None:
        # Arrange
        video_id = fxt_mongo_id(1)
        video = MagicMock()
        video.preprocessing = MediaPreprocessing(status=preprocessing_status)

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video) as mock_get_by_id,
            pytest.raises(MediaNotPreprocessedException),
        ):
            MediaManager.get_video_thumbnail_frame_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=video_id,
                frame_index=1,
            )
        # Assert
        mock_get_by_id.assert_called_once_with(video_id)

    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_get_video_thumbnail_frame_by_id_async_preprocessing(self, fxt_dataset_storage, fxt_mongo_id) -> None:
        # Arrange
        video_id = fxt_mongo_id(1)
        video = MagicMock()
        video.preprocessing = MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED)
        video_frame = MagicMock()

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video) as mock_get_by_id,
            patch.object(
                MediaManager, "get_single_thumbnail_frame_numpy", return_value=video_frame
            ) as mock_get_single_thumbnail_frame_numpy,
        ):
            np_frame = MediaManager.get_video_thumbnail_frame_by_id(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=video_id,
                frame_index=1,
            )
        # Assert
        mock_get_by_id.assert_called_once_with(video_id)
        mock_get_single_thumbnail_frame_numpy.assert_called_once_with(
            video=video, dataset_storage_identifier=fxt_dataset_storage.identifier, frame_index=1
        )
        assert np_frame == video_frame

    @pytest.mark.parametrize(
        "preprocessing_status",
        [MediaPreprocessingStatus.SCHEDULED, MediaPreprocessingStatus.IN_PROGRESS, MediaPreprocessingStatus.FAILED],
    )
    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_get_image_thumbnail_async_preprocessing_not_ready(
        self, fxt_dataset_storage, fxt_mongo_id, preprocessing_status
    ) -> None:
        # Arrange
        image_id = fxt_mongo_id(1)
        image = MagicMock()
        image.preprocessing = MediaPreprocessing(status=preprocessing_status)

        # Act
        with (
            patch.object(ImageRepo, "get_by_id", return_value=image) as mock_get_by_id,
            pytest.raises(MediaNotPreprocessedException),
        ):
            MediaManager.get_image_thumbnail(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                image_id=image_id,
            )
        # Assert
        mock_get_by_id.assert_called_once_with(image_id)

    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_get_image_thumbnail_async_preprocessing(self, fxt_dataset_storage, fxt_mongo_id) -> None:
        # Arrange
        image_id = fxt_mongo_id(1)
        image = MagicMock()
        image.preprocessing = MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED)
        thumbnail = MagicMock()

        # Act
        with (
            patch.object(ImageRepo, "get_by_id", return_value=image) as mock_get_by_id,
            patch.object(ThumbnailBinaryRepo, "get_by_filename", return_value=thumbnail) as mock_get_by_filename,
        ):
            result = MediaManager.get_image_thumbnail(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                image_id=image_id,
            )
        # Assert
        mock_get_by_id.assert_called_once_with(image_id)
        mock_get_by_filename.assert_called_once_with(
            filename=f"{image_id}_thumbnail.jpg",
            binary_interpreter=ANY,
        )
        assert result == thumbnail

    @pytest.mark.parametrize(
        "preprocessing_status",
        [MediaPreprocessingStatus.SCHEDULED, MediaPreprocessingStatus.IN_PROGRESS, MediaPreprocessingStatus.FAILED],
    )
    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_get_video_thumbnail_async_preprocessing_not_ready(
        self, fxt_dataset_storage, fxt_mongo_id, preprocessing_status
    ) -> None:
        # Arrange
        video_id = fxt_mongo_id(1)
        video = MagicMock()
        video.preprocessing = MediaPreprocessing(status=preprocessing_status)

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video) as mock_get_by_id,
            pytest.raises(MediaNotPreprocessedException),
        ):
            MediaManager.get_video_thumbnail(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=video_id,
            )
        # Assert
        mock_get_by_id.assert_called_once_with(video_id)

    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_get_video_thumbnail_async_preprocessing(self, fxt_dataset_storage, fxt_mongo_id) -> None:
        # Arrange
        video_id = fxt_mongo_id(1)
        video = MagicMock()
        video.preprocessing = MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED)
        thumbnail = MagicMock()

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video) as mock_get_by_id,
            patch.object(ThumbnailBinaryRepo, "get_by_filename", return_value=thumbnail) as mock_get_by_filename,
        ):
            result = MediaManager.get_video_thumbnail(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=video_id,
            )
        # Assert
        mock_get_by_id.assert_called_once_with(video_id)
        mock_get_by_filename.assert_called_once_with(
            filename=f"{video_id}_thumbnail.jpg",
            binary_interpreter=ANY,
        )
        assert result == thumbnail

    @pytest.mark.parametrize(
        "preprocessing_status",
        [MediaPreprocessingStatus.SCHEDULED, MediaPreprocessingStatus.IN_PROGRESS, MediaPreprocessingStatus.FAILED],
    )
    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_get_video_thumbnail_stream_location_async_preprocessing_not_ready(
        self, fxt_dataset_storage, fxt_mongo_id, preprocessing_status
    ) -> None:
        # Arrange
        video_id = fxt_mongo_id(1)
        video = MagicMock()
        video.preprocessing = MediaPreprocessing(status=preprocessing_status)

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video) as mock_get_by_id,
            pytest.raises(MediaNotPreprocessedException),
        ):
            MediaManager.get_video_thumbnail_stream_location(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=video_id,
            )
        # Assert
        mock_get_by_id.assert_called_once_with(video_id)

    @patch.dict(os.environ, {"FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "true"})
    def test_get_video_thumbnail_stream_location_async_preprocessing(self, fxt_dataset_storage, fxt_mongo_id) -> None:
        # Arrange
        video_id = fxt_mongo_id(1)
        video = MagicMock()
        video.preprocessing = MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED)

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video) as mock_get_by_id,
            patch.object(
                ThumbnailBinaryRepo, "get_path_or_presigned_url", return_value="presigned_url"
            ) as mock_get_path_or_presigned_url,
        ):
            result = MediaManager.get_video_thumbnail_stream_location(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                video_id=video_id,
            )
        # Assert
        mock_get_by_id.assert_called_once_with(video_id)
        mock_get_path_or_presigned_url.assert_called_once_with(filename=f"{video_id}_thumbnail.mp4")
        assert result == "presigned_url"

    def test_delete_image_by_id(self, fxt_empty_project_persisted, fxt_image_entity) -> None:
        dataset_storage = fxt_empty_project_persisted.get_training_dataset_storage()
        with (
            patch.object(MediaManager, "get_image_by_id", return_value=fxt_image_entity) as mock_get_image,
            patch.object(DeletionHelpers, "delete_image_entity") as mock_delete_image,
        ):
            MediaManager.delete_image_by_id(
                project=fxt_empty_project_persisted,
                dataset_storage=dataset_storage,
                image_id=fxt_image_entity.id_,
            )

            mock_get_image.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier,
                image_id=fxt_image_entity.id_,
            )
            mock_delete_image.assert_called_once_with(dataset_storage=dataset_storage, image=fxt_image_entity)

    def test_delete_video_by_id(self, fxt_empty_project_persisted, fxt_video_entity) -> None:
        dataset_storage = fxt_empty_project_persisted.get_training_dataset_storage()
        with (
            patch.object(MediaManager, "get_video_by_id", return_value=fxt_video_entity) as mock_get_video,
            patch.object(DeletionHelpers, "delete_video_entity") as mock_delete_video,
        ):
            MediaManager.delete_video_by_id(
                project=fxt_empty_project_persisted,
                dataset_storage=dataset_storage,
                video_id=fxt_video_entity.id_,
            )

            mock_get_video.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier,
                video_id=fxt_video_entity.id_,
            )
            mock_delete_video.assert_called_once_with(dataset_storage=dataset_storage, video=fxt_video_entity)

    def test_delete_media_project_locked(self, fxt_empty_project_persisted, fxt_image_entity, fxt_video_entity) -> None:
        dataset_storage = fxt_empty_project_persisted.get_training_dataset_storage()
        ProjectRepo().mark_locked(
            owner="test",
            project_id=fxt_empty_project_persisted.id_,
            duration_seconds=1000,
        )
        with pytest.raises(ProjectLockedException):
            MediaManager.delete_image_by_id(
                project=fxt_empty_project_persisted,
                dataset_storage=dataset_storage,
                image_id=fxt_image_entity.id_,
            )

        with pytest.raises(ProjectLockedException):
            MediaManager.delete_video_by_id(
                project=fxt_empty_project_persisted,
                dataset_storage=dataset_storage,
                video_id=fxt_video_entity.id_,
            )

    def test_get_video_frame_thumbnail_numpy(
        self, fxt_dataset_storage_identifier, fxt_mongo_id, fxt_media_numpy
    ) -> None:
        with patch.object(MediaManager, "get_video_frame_by_id", return_value=fxt_media_numpy) as mock_get_image:
            result = MediaManager().get_video_frame_thumbnail_numpy(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video_id=ID(fxt_mongo_id()),
                frame_index=0,
                target_height=10,
                target_width=20,
            )
        mock_get_image.assert_called_once_with(
            dataset_storage_identifier=fxt_dataset_storage_identifier,
            video_id=ID(fxt_mongo_id()),
            frame_index=0,
        )
        assert result.shape == (10, 20, 3)

    def test_create_and_save_thumbnail_video_already_exists(
        self, fxt_dataset_storage_identifier, fxt_video_entity
    ) -> None:
        with (
            patch.object(ThumbnailBinaryRepo, "exists", return_value=True) as patch_exists,
            patch.object(ThumbnailBinaryRepo, "create_path_for_temporary_file", return_value=None) as patch_create_path,
        ):
            MediaManager().create_and_save_thumbnail_video(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video=fxt_video_entity,
            )

            patch_exists.assert_called_once_with(filename=fxt_video_entity.thumbnail_video_filename)
            patch_create_path.assert_not_called()

    def test_create_and_save_thumbnail_video(self, fxt_dataset_storage_identifier, fxt_video_entity) -> None:
        with (
            patch.object(ThumbnailBinaryRepo, "exists", return_value=False) as patch_exists,
            patch.object(
                ThumbnailBinaryRepo,
                "create_path_for_temporary_file",
                return_value="dummy_tmp_path",
            ) as patch_create_path,
            patch.object(
                VideoBinaryRepo,
                "get_path_or_presigned_url",
                return_value="dummy_presigned_url",
            ) as patch_get_presigned_url,
            patch.object(ThumbnailBinaryRepo, "save", return_value=None) as patch_save,
        ):
            MediaManager().create_and_save_thumbnail_video(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video=fxt_video_entity,
            )

            patch_exists.assert_called_once_with(filename=fxt_video_entity.thumbnail_video_filename)
            patch_create_path.assert_called_once_with(
                filename=fxt_video_entity.thumbnail_video_filename, make_unique=False
            )
            patch_get_presigned_url.assert_called_once_with(filename=fxt_video_entity.data_binary_filename)
            patch_save.assert_called_once_with(
                data_source="dummy_tmp_path",
                remove_source=True,
                dst_file_name=fxt_video_entity.thumbnail_video_filename,
            )

    def test_get_presigned_url_for_video(self, fxt_dataset_storage_identifier, fxt_video_entity) -> None:
        with (
            patch.object(VideoRepo, "get_by_id", return_value=fxt_video_entity) as mock_get_by_id,
            patch.object(
                VideoBinaryRepo,
                "get_path_or_presigned_url",
                return_value="dummy_presigned_url",
            ) as mock_get_presigned_url,
        ):
            MediaManager().get_path_or_presigned_url_for_video(
                dataset_storage_identifier=fxt_dataset_storage_identifier,
                video_id=fxt_video_entity.id_,
            )
            mock_get_by_id.assert_called_once_with(fxt_video_entity.id_)
            video_name = f"{fxt_video_entity.name}{fxt_video_entity.extension.value}"
            mock_get_presigned_url.assert_called_once_with(
                filename=fxt_video_entity.data_binary_filename,
                preset_headers={"response-content-disposition": f'attachment; filename="{video_name}"'},
            )

    def test_get_thumbnail_video_stream_location(
        self,
        request,
        fxt_project,
        fxt_unannotated_video_factory,
    ) -> None:
        """
        This test saves a video without a thumbnail video, requests the thumbnail and then checks that the
        thumbnail video generation is started.
        """
        # Hook for event publishing
        patch_publish_event = patch("resource_management.media_manager.publish_event", side_effect=publish_event)

        dataset_storage = fxt_project.get_training_dataset_storage()
        video = fxt_unannotated_video_factory(project=fxt_project, width=20, height=20, number_of_frames=6)

        with (
            patch.object(MediaManager, "get_video_by_id", return_value=video) as mock_get_video_by_id,
            patch_publish_event as patched_pub_video_gen,
            pytest.raises(VideoThumbnailNotFoundException),
        ):
            MediaManager.get_video_thumbnail_stream_location(
                dataset_storage_identifier=dataset_storage.identifier,
                video_id=video.id_,
            )

            mock_get_video_by_id.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier,
                video_id=video.id_,
            )
            patched_pub_video_gen.assert_called_once_with(
                topic="thumbnail_video_missing",
                body={
                    "workspace_id": fxt_project.workspace_id,
                    "project_id": dataset_storage.identifier.project_id,
                    "dataset_storage_id": fxt_project.get_training_dataset_storage().id_,
                    "video_id": video.id_,
                },
                key=str(video.id_).encode(),
                headers_getter=ANY,
            )
