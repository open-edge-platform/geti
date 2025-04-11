# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
import copy
from io import BytesIO
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi import UploadFile
from testfixtures import compare

from communication.exceptions import (
    LabelNotFoundException,
    MediaUploadedWithNoLabelToAnomalyTaskException,
    VideoThumbnailNotFoundException,
)
from communication.rest_controllers import MediaRESTController
from communication.rest_views.filtered_dataset_rest_views import FilteredDatasetRESTView
from communication.rest_views.media_rest_views import MediaRESTViews
from managers.annotation_manager import AnnotationManager
from managers.project_manager import ProjectManager
from resource_management.media_manager import MediaManager
from service.label_schema_service import LabelSchemaService
from usecases.query_builder import QueryResults

from geti_fastapi_tools.exceptions import InvalidMediaException
from geti_fastapi_tools.responses import success_response_rest
from geti_kafka_tools import publish_event
from geti_types import ID, DatasetStorageIdentifier, MediaType
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.label import NullLabel
from sc_sdk.entities.label_schema import LabelSchema, NullLabelSchema
from sc_sdk.entities.media import ImageExtensions, VideoExtensions
from sc_sdk.entities.video_annotation_statistics import VideoAnnotationStatistics
from sc_sdk.repos import DatasetRepo, LabelRepo, LabelSchemaRepo, VideoRepo
from sc_sdk.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from sc_sdk.repos.storage.storage_client import BytesStream
from sc_sdk.services.dataset_storage_filter_service import DatasetStorageFilterService


class TestMediaRESTController:
    def test_get_image_detail(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_image_entity,
        fxt_media_states_per_task,
        fxt_image_identifier_rest,
    ) -> None:
        image_id = fxt_mongo_id(1)
        dataset_storage = fxt_project.get_training_dataset_storage()
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(MediaManager, "get_image_by_id", return_value=fxt_image_entity) as mock_get_image_by_id,
            patch.object(
                AnnotationManager,
                "get_media_states_per_task",
                return_value=fxt_media_states_per_task,
            ) as mock_get_media_states_per_task,
            patch.object(
                MediaRESTViews,
                "media_to_rest",
                return_value=fxt_image_identifier_rest,
            ) as mock_media_to_rest,
        ):
            result = MediaRESTController.get_image_detail(
                dataset_storage_identifier=dataset_storage.identifier,
                image_id=image_id,
            )

            mock_get_project_by_id.assert_called_with(project_id=dataset_storage.identifier.project_id)
            mock_get_image_by_id.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier, image_id=image_id
            )
            mock_get_media_states_per_task.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier,
                media_identifiers=[fxt_image_entity.media_identifier],
                project=fxt_project,
            )
            mock_media_to_rest.assert_called_once_with(
                media=fxt_image_entity,
                media_identifier=fxt_image_entity.media_identifier,
                annotation_state_per_task=fxt_media_states_per_task.get(fxt_image_entity.media_identifier),
                dataset_storage_identifier=dataset_storage.identifier,
            )
            compare(result, fxt_image_identifier_rest, ignore_eq=True)

    def test_get_video_detail(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_video_entity,
        fxt_media_states_per_task,
        fxt_video_identifier_rest,
    ) -> None:
        video_id = fxt_mongo_id(1)
        video_annotation_stat = VideoAnnotationStatistics(annotated=4, partially_annotated=3, unannotated=2)

        dataset_storage = fxt_project.get_training_dataset_storage()
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(MediaManager, "get_video_by_id", return_value=fxt_video_entity) as mock_get_video_by_id,
            patch.object(
                AnnotationManager,
                "get_media_states_per_task",
                return_value=fxt_media_states_per_task,
            ) as mock_get_media_states_per_task,
            patch.object(
                MediaRESTViews,
                "media_to_rest",
                return_value=fxt_video_identifier_rest,
            ) as mock_media_to_rest,
            patch.object(
                DatasetStorageFilterRepo,
                "get_video_annotation_statistics_by_ids",
                return_value={video_id: video_annotation_stat},
            ) as mock_video_stats,
        ):
            result = MediaRESTController.get_video_detail(
                dataset_storage_identifier=dataset_storage.identifier,
                video_id=video_id,
            )

            mock_get_project_by_id.assert_called_once_with(project_id=dataset_storage.identifier.project_id)
            mock_get_video_by_id.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier, video_id=video_id
            )
            mock_get_media_states_per_task.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier,
                media_identifiers=[fxt_video_entity.media_identifier],
                project=fxt_project,
            )
            mock_media_to_rest.assert_called_once_with(
                media=fxt_video_entity,
                media_identifier=fxt_video_entity.media_identifier,
                annotation_state_per_task=fxt_media_states_per_task.get(fxt_video_entity.media_identifier),
                dataset_storage_identifier=dataset_storage.identifier,
                video_annotation_statistics=video_annotation_stat,
            )
            mock_video_stats.assert_called_once_with([video_id])
            compare(result, fxt_video_identifier_rest, ignore_eq=True)

    def test_download_video_frame(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_image_entity,
    ) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        video_id = fxt_mongo_id(1)
        frame_index = 5

        with patch.object(
            MediaManager, "get_video_frame_by_id", return_value=fxt_image_entity
        ) as mock_get_video_frame_by_id:
            result = MediaRESTController.download_video_frame(
                dataset_storage_identifier=dataset_storage.identifier,
                video_id=video_id,
                frame_index=frame_index,
            )
        mock_get_video_frame_by_id.assert_called_once_with(
            dataset_storage_identifier=dataset_storage.identifier,
            video_id=video_id,
            frame_index=frame_index,
        )
        assert result == fxt_image_entity

    def test_download_video_frame_thumbnail(self, fxt_mongo_id, fxt_project, fxt_media_numpy) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        video_id = fxt_mongo_id(1)
        frame_index = 5

        with patch.object(
            MediaManager,
            "get_video_thumbnail_frame_by_id",
            return_value=fxt_media_numpy,
        ) as mock_get_video_frame_thumbnail_numpy:
            result = MediaRESTController.download_video_frame_thumbnail(
                dataset_storage_identifier=dataset_storage.identifier,
                video_id=video_id,
                frame_index=frame_index,
            )

        mock_get_video_frame_thumbnail_numpy.assert_called_once_with(
            dataset_storage_identifier=dataset_storage.identifier,
            video_id=video_id,
            frame_index=frame_index,
        )
        assert (result == fxt_media_numpy).all()

    def test_download_video_stream(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_dataset_storage,
    ) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        video_id = fxt_mongo_id(4)
        dummy_path = Path("dummy/path")

        with patch.object(
            MediaManager, "get_path_or_presigned_url_for_video", return_value=dummy_path
        ) as mock_get_binary_path_of_video:
            result = MediaRESTController.download_video_stream(
                dataset_storage_identifier=dataset_storage.identifier,
                video_id=video_id,
            )
        mock_get_binary_path_of_video.assert_called_once_with(
            dataset_storage_identifier=dataset_storage.identifier,
            video_id=video_id,
        )
        assert result == dummy_path

    def test_parse_and_validate_media_filename(self) -> None:
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "foo.bmp"

        basename, ext = MediaRESTController._parse_and_validate_media_filename(upload_file=upload_file)

        assert basename == "foo"
        assert ext == ".bmp"

    @pytest.mark.parametrize("filename", [None, " ", "foo", " .bmp"])
    def test_parse_and_validate_media_filename_invalid(self, filename) -> None:
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = filename

        with pytest.raises(InvalidMediaException):
            MediaRESTController._parse_and_validate_media_filename(upload_file=upload_file)

    def test_resolve_image_extension(self) -> None:
        resolved_ext = MediaRESTController._resolve_image_extension(".bmp")

        assert resolved_ext == ImageExtensions.BMP

    def test_resolve_video_extension(self) -> None:
        resolved_ext = MediaRESTController._resolve_video_extension(".mp4")

        assert resolved_ext == VideoExtensions.MP4

    def test_upload_media_error_labels_for_nonglobal_task(
        self,
        fxt_project_with_segmentation_task,
        fxt_label,
    ) -> None:
        project_id = fxt_project_with_segmentation_task.id_
        workspace_id = fxt_project_with_segmentation_task.workspace_id
        dataset_storage_id = fxt_project_with_segmentation_task.training_dataset_storage_id
        dataset_storage_identifier = DatasetStorageIdentifier(workspace_id, project_id, dataset_storage_id)
        media_type = MediaType.IMAGE
        dummy_values = {"key1": "value1", "key2": "value2"}
        dummy_file_storage = MagicMock()
        dummy_file_storage.filename = "foo.jpg"
        dummy_file_storage.file.read = MagicMock(return_value=b"data")
        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project_with_segmentation_task,
            ) as mock_get_project_by_id,
            patch.object(
                MediaRESTController,
                "get_label_from_upload_request",
                return_value=[fxt_label],
            ) as mock_get_label_from_upload_request,
            pytest.raises(NotImplementedError) as error,
        ):
            MediaRESTController.upload_media(
                dataset_storage_identifier=dataset_storage_identifier,
                user_id=ID("dummy_user"),
                media_type=media_type,
                label_info=dummy_values,
                file_from_request=dummy_file_storage,
            )
        mock_get_project_by_id.assert_called_once_with(project_id=project_id)
        mock_get_label_from_upload_request.assert_called_once_with(
            dummy_values, fxt_project_with_segmentation_task.identifier
        )
        assert (
            str(error.value)
            == "Uploading media with labels to a task that does not support global labels is not allowed."
        )

    def test_upload_media_image(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_media_entities_list,
        fxt_media_identifier_rest,
    ) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        media_type = MediaType.IMAGE
        dummy_values = {
            "key1": "value1",
            "key2": "value2",
        }

        bytes_data = b"dummy_stream"
        file_data = BytesIO(bytes_data)
        dummy_file = UploadFile(filename="dummy_filename.jpg", file=file_data, size=len(bytes_data))

        with (
            patch("communication.rest_controllers.media_controller.publish_event") as mock_publish_event,
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(
                MediaRESTController, "get_label_from_upload_request", return_value=[]
            ) as mock_get_label_from_upload_request,
            patch.object(MediaManager, "upload_image", return_value=fxt_media_entities_list[0]) as mock_upload_image,
            patch.object(
                MediaRESTViews,
                "media_to_rest",
                return_value=fxt_media_identifier_rest,
            ) as mock_media_to_rest,
            patch.object(
                DatasetStorageFilterService, "on_new_media_upload", return_value=None
            ) as mock_update_dataset_storage_filter_data,
        ):
            result = MediaRESTController.upload_media(
                dataset_storage_identifier=dataset_storage.identifier,
                user_id=ID("dummy_user"),
                media_type=media_type,
                label_info=dummy_values,
                file_from_request=dummy_file,
            )
        mock_get_project_by_id.assert_called_once_with(project_id=dataset_storage.project_id)
        mock_get_label_from_upload_request.assert_called_once_with(dummy_values, fxt_project.identifier)

        mock_upload_image.assert_called_once_with(
            dataset_storage_identifier=dataset_storage.identifier,
            basename="dummy_filename",
            extension=ImageExtensions.JPG,
            data_stream=BytesStream(data=file_data, length=len(bytes_data)),
            user_id=ID("dummy_user"),
            update_metrics=False,
        )
        mock_publish_event.assert_called_once_with(
            topic="media_uploads",
            body={
                "workspace_id": dataset_storage.identifier.workspace_id,
                "project_id": dataset_storage.identifier.project_id,
                "dataset_storage_id": dataset_storage.identifier.dataset_storage_id,
                "media_id": fxt_media_entities_list[0].id_,
                "media_type": fxt_media_entities_list[0].media_identifier.media_type.value,
            },
            key=str(fxt_media_entities_list[0].id_).encode(),
            headers_getter=ANY,
        )
        mock_media_to_rest.assert_called_once_with(
            media=fxt_media_entities_list[0],
            media_identifier=fxt_media_entities_list[0].media_identifier,
            annotation_state_per_task=ANY,
            dataset_storage_identifier=dataset_storage.identifier,
            video_annotation_statistics=None,
        )
        mock_update_dataset_storage_filter_data.assert_called_once_with(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_id=fxt_media_entities_list[0].id_,
            media_type=media_type,
        )

        compare(result, fxt_media_identifier_rest, ignore_eq=True)

    def test_upload_media_video(
        self,
        fxt_mongo_id,
        fxt_project,
        fxt_media_entities_list,
        fxt_media_identifier_rest,
    ) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        media_type = MediaType.VIDEO
        dummy_values = {
            "key1": "value1",
            "key2": "value2",
        }
        bytes_data = b"dummy_stream"
        file_data = BytesIO(bytes_data)
        dummy_file = UploadFile(filename="dummy_filename.mp4", file=file_data, size=len(bytes_data))
        video_entity = fxt_media_entities_list[1]

        with (
            patch("communication.rest_controllers.media_controller.publish_event") as mock_publish_event,
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(
                MediaRESTController, "get_label_from_upload_request", return_value=[]
            ) as mock_get_label_from_upload_request,
            patch.object(MediaManager, "upload_video", return_value=video_entity) as mock_upload_video,
            patch.object(
                MediaRESTViews,
                "media_to_rest",
                return_value=fxt_media_identifier_rest,
            ) as mock_media_to_rest,
            patch.object(
                DatasetStorageFilterService, "on_new_media_upload", return_value=None
            ) as mock_update_dataset_storage_filter_data,
        ):
            result = MediaRESTController.upload_media(
                dataset_storage_identifier=dataset_storage.identifier,
                user_id=ID("dummy_id"),
                media_type=media_type,
                label_info=dummy_values,
                file_from_request=dummy_file,
            )
        mock_get_project_by_id.assert_called_once_with(project_id=dataset_storage.project_id)
        mock_get_label_from_upload_request.assert_called_once_with(dummy_values, fxt_project.identifier)

        mock_upload_video.assert_called_once_with(
            dataset_storage_identifier=dataset_storage.identifier,
            basename="dummy_filename",
            extension=VideoExtensions.MP4,
            data_stream=BytesStream(data=file_data, length=len(bytes_data)),
            user_id=ID("dummy_id"),
            update_metrics=False,
        )
        mock_media_to_rest.assert_called_once_with(
            media=video_entity,
            media_identifier=video_entity.media_identifier,
            annotation_state_per_task=ANY,
            dataset_storage_identifier=dataset_storage.identifier,
            video_annotation_statistics=VideoAnnotationStatistics(
                annotated=0,
                partially_annotated=0,
                unannotated=video_entity.total_frames,
            ),
        )
        mock_publish_event.assert_called_once_with(
            topic="media_uploads",
            body={
                "workspace_id": dataset_storage.identifier.workspace_id,
                "project_id": dataset_storage.identifier.project_id,
                "dataset_storage_id": dataset_storage.identifier.dataset_storage_id,
                "media_id": video_entity.id_,
                "media_type": video_entity.media_identifier.media_type.value,
            },
            key=str(video_entity.id_).encode(),
            headers_getter=ANY,
        )
        mock_update_dataset_storage_filter_data.assert_called_once_with(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_id=video_entity.id_,
            media_type=media_type,
        )

        compare(result, fxt_media_identifier_rest, ignore_eq=True)

    def test_get_label_from_upload_request(
        self,
        fxt_project,
        fxt_label,
    ) -> None:
        label1 = fxt_label
        label2 = copy.deepcopy(fxt_label)
        label2.name = "new_name"

        dummy_rest_values_data = {"label_ids": ["id1", "id2"]}

        with patch.object(
            MediaRESTController, "get_labels_by_ids", return_value=[label1, label2]
        ) as mock_get_labels_by_ids:
            result = MediaRESTController.get_label_from_upload_request(
                project_identifier=fxt_project.identifier,
                upload_info=dummy_rest_values_data,
            )
        mock_get_labels_by_ids.assert_called_once_with(
            label_ids=[ID("id1"), ID("id2")],
            project_identifier=fxt_project.identifier,
        )

        assert result == [label1, label2]

    @pytest.mark.skip(reason="CVS-91533: SDK incompatible behavior; re-enable after CVS-91571")
    def test_get_label_from_upload_request_fail(
        self,
        fxt_project_with_anomaly_detection_task,
    ) -> None:
        dummy_rest_values_data = {"label_ids": []}  # type: ignore
        project_identifier = fxt_project_with_anomaly_detection_task.identifier
        with pytest.raises(MediaUploadedWithNoLabelToAnomalyTaskException):
            MediaRESTController.get_label_from_upload_request(
                project_identifier=project_identifier,
                upload_info=dummy_rest_values_data,
            )
        dummy_rest_values_data = {}
        with pytest.raises(MediaUploadedWithNoLabelToAnomalyTaskException):
            MediaRESTController.get_label_from_upload_request(
                project_identifier=project_identifier,
                upload_info=dummy_rest_values_data,
            )

    def test_delete_image(self, fxt_project, fxt_mongo_id) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        image_id = fxt_mongo_id(0)
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(MediaManager, "delete_image_by_id") as mock_delete_image_by_id,
        ):
            result = MediaRESTController.delete_image(
                dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
                image_id=image_id,
            )

            mock_get_project.assert_called_once_with(project_id=dataset_storage.project_id)
            mock_delete_image_by_id.assert_called_once_with(
                project=fxt_project,
                dataset_storage=fxt_project.get_training_dataset_storage(),
                image_id=ID(image_id),
            )
            compare(result, success_response_rest(), ignore_eq=True)

    def test_delete_video(self, fxt_project, fxt_mongo_id) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        video_id = fxt_mongo_id(0)
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(MediaManager, "delete_video_by_id") as mock_delete_video_by_id,
        ):
            result = MediaRESTController.delete_video(
                dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
                video_id=video_id,
            )

            mock_get_project.assert_called_once_with(project_id=dataset_storage.project_id)
            mock_delete_video_by_id.assert_called_once_with(
                project=fxt_project,
                dataset_storage=fxt_project.get_training_dataset_storage(),
                video_id=ID(video_id),
            )
            compare(result, success_response_rest(), ignore_eq=True)

    def test_get_image_thumbnail(self, request) -> None:
        """
        This test creates an image without a thumbnail, requests the thumbnail and then checks that the thumbnail is
        generated.
        """
        dataset_storage_identifier = MagicMock()
        image_id = MagicMock()
        image_thumbnail = MagicMock()

        with patch.object(
            MediaManager, "get_image_thumbnail", return_value=image_thumbnail
        ) as mock_get_image_thumbnail:
            thumbnail = MediaRESTController.get_image_thumbnail(
                dataset_storage_identifier=dataset_storage_identifier,
                image_id=image_id,
            )

            mock_get_image_thumbnail.assert_called_once_with(
                dataset_storage_identifier=dataset_storage_identifier,
                image_id=image_id,
            )
            assert thumbnail == image_thumbnail

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
        patch_publish_event = patch(
            "communication.rest_controllers.media_controller.publish_event",
            side_effect=publish_event,
        )

        dataset_storage = fxt_project.get_training_dataset_storage()
        video = fxt_unannotated_video_factory(project=fxt_project, width=20, height=20, number_of_frames=6)

        with (
            patch.object(MediaManager, "get_video_by_id", return_value=video) as mock_get_video_by_id,
            patch_publish_event as patched_pub_video_gen,
            pytest.raises(VideoThumbnailNotFoundException),
        ):
            MediaRESTController.get_video_thumbnail_stream_location(
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

    @pytest.mark.parametrize(
        "lazyfxt_dataset_id, lazyfxt_video_id, expected_called_rest_view",
        [
            ("fxt_mongo_id", "fxt_mongo_id", "filtered_dataset_for_video_to_rest"),
            ("fxt_mongo_id", None, "filtered_dataset_to_rest"),
            (None, "fxt_mongo_id", "filtered_frames_to_rest"),
            (None, None, "filtered_dataset_storage_to_rest"),
        ],
        ids=[
            "video and dataset specified",
            "only dataset specified",
            "only video specified",
            "video and dataset not specified",
        ],
    )
    def test_get_filtered_items(
        self,
        lazyfxt_dataset_id,
        lazyfxt_video_id,
        expected_called_rest_view,
        request,
        fxt_mongo_id,
        fxt_project,
        fxt_dataset_filter,
        fxt_empty_query_results,
        fxt_video_entity,
    ) -> None:
        """
        This test saves a video without a thumbnail video, requests the thumbnail path
        and then checks that the thumbnail video generation is started.
        """
        dataset_storage = fxt_project.get_training_dataset_storage()
        if lazyfxt_video_id is not None:
            lazyfxt_video_id = request.getfixturevalue(lazyfxt_video_id)(0)
        if lazyfxt_dataset_id is not None:
            lazyfxt_dataset_id = request.getfixturevalue(lazyfxt_dataset_id)(1)

        dataset = MagicMock(spec=Dataset)
        dataset.purpose = DatasetPurpose.TRAINING
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(
                ProjectManager,
                "get_dataset_storage_by_id",
                return_value=dataset_storage,
            ) as mock_get_dataset_storage_by_id,
            patch.object(DatasetRepo, "get_by_id", return_value=dataset) as mock_get_dataset,
            patch.object(
                AnnotationManager,
                "get_media_states_per_task",
                return_value={"dummy1": "dummy1"},
            ) as mock_get_media_states,
            patch.object(
                FilteredDatasetRESTView,
                expected_called_rest_view,
                return_value={"dummy2": "dummy2"},
            ) as mock_to_rest,
            patch.object(VideoRepo, "get_by_id", return_value=fxt_video_entity),
        ):
            MediaRESTController.get_filtered_items(
                dataset_storage_identifier=dataset_storage.identifier,
                dataset_filter=fxt_dataset_filter,
                dataset_id=lazyfxt_dataset_id,
                video_id=lazyfxt_video_id,
                fps=1,
            )

            mock_get_project_by_id.assert_called_once_with(project_id=dataset_storage.project_id)
            mock_get_dataset_storage_by_id.assert_called_once_with(
                project=fxt_project, dataset_storage_id=dataset_storage.id_
            )
            if lazyfxt_dataset_id:
                mock_get_dataset.assert_called_once()
            else:
                mock_get_dataset.assert_not_called()
            mock_get_media_states.assert_called_once_with(
                project=fxt_project,
                dataset_storage_identifier=dataset_storage.identifier,
                media_identifiers=[],
            )
            mock_to_rest.assert_called_once()
            expected_call = {
                "dataset_storage_identifier": dataset_storage.identifier,
                "query_results": fxt_empty_query_results,
                "dataset_filter": fxt_dataset_filter,
                "media_annotation_states_per_task": {"dummy1": "dummy1"},
            }
            if lazyfxt_dataset_id:
                expected_call["dataset_id"] = lazyfxt_dataset_id
                if lazyfxt_video_id:
                    expected_call["video_id"] = lazyfxt_video_id
            if expected_called_rest_view == "filtered_frames_to_rest":
                expected_call["video"] = fxt_video_entity
                expected_call["video_frame_indices"] = []
                expected_call["include_frame_details"] = False
                expected_call["query_results"] = QueryResults(
                    media_query_results=[],
                    skip=100,
                    matching_images_count=0,
                    matching_videos_count=1,
                    matching_video_frames_count=0,
                    total_images_count=0,
                    total_videos_count=0,
                )

            assert mock_to_rest.mock_calls[0].kwargs == expected_call

    def test_get_label_by_id(self, fxt_project, fxt_label_schema, fxt_label) -> None:
        # Arrange
        label_id = fxt_label.id_

        # Act
        with (
            patch.object(LabelSchema, "get_all_labels", return_value=[fxt_label]) as patched_get_labels,
            patch.object(LabelSchemaRepo, "get_latest", return_value=fxt_label_schema),
        ):
            result = MediaRESTController.get_labels_by_ids(
                label_ids=[label_id],
                project_identifier=fxt_project.identifier,
            )[0]

        # Assert
        patched_get_labels.assert_called_once_with()
        assert result == fxt_label

    def test_get_label_by_id_not_found(self, fxt_project, fxt_label_schema) -> None:
        # Arrange
        label_id = ID("label_id_123")

        with (
            patch.object(LabelSchema, "get_all_labels", return_value=[NullLabel()]),
            patch.object(LabelSchemaRepo, "get_latest", return_value=fxt_label_schema),
            pytest.raises(LabelNotFoundException),
        ):
            # Act & Assert
            MediaRESTController.get_labels_by_ids(
                label_ids=[label_id],
                project_identifier=fxt_project.identifier,
            )

    def test_get_label_by_id_no_label_schema(self, fxt_project, fxt_label) -> None:
        # Arrange
        label_id = ID("label_id_123")

        with (
            patch.object(LabelRepo, "get_by_id", return_value=fxt_label),
            patch.object(LabelSchemaRepo, "get_latest", return_value=NullLabelSchema()),
            pytest.raises(RuntimeError),
        ):
            # Act & Assert
            MediaRESTController.get_labels_by_ids(
                label_ids=[label_id],
                project_identifier=fxt_project.identifier,
            )

    def test_get_label_by_id_not_in_project(self, fxt_project, fxt_mongo_id, fxt_classification_label_schema) -> None:
        # Arrange
        label_id = fxt_mongo_id(123)
        label_schema = fxt_classification_label_schema

        with (
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_project",
                return_value=label_schema,
            ),
            pytest.raises(LabelNotFoundException),
        ):
            # Act & Assert
            MediaRESTController.get_labels_by_ids(
                label_ids=[label_id],
                project_identifier=fxt_project.identifier,
            )
