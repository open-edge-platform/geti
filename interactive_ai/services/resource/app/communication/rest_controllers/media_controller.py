# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the media controller"""

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

import numpy as np
from fastapi import UploadFile

from communication.exceptions import (
    LabelNotFoundException,
    NoMediaInProjectException,
    TrainingRevisionNotFoundException,
    UnexpectedDatasetPurposeException,
    VideoThumbnailNotFoundException,
)
from communication.limit_check_helpers import check_max_number_of_media_files
from communication.rest_utils import T
from communication.rest_views.filtered_dataset_rest_views import FilteredDatasetRESTView
from communication.rest_views.media_rest_views import MediaRESTViews
from managers.annotation_manager import AnnotationManager
from managers.project_manager import ProjectManager
from resource_management import VideoRangeAnnotationManager
from resource_management.media_manager import MediaManager
from service.label_schema_service import LabelSchemaService
from usecases.dataset_filter import DatasetFilter
from usecases.query_builder import QueryBuilder, QueryResults

from geti_fastapi_tools.exceptions import InvalidMediaException
from geti_fastapi_tools.responses import success_response_rest
from geti_kafka_tools import publish_event
from geti_telemetry_tools import ENABLE_METRICS, unified_tracing
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, MediaType, ProjectIdentifier, Singleton
from geti_types.session import add_extra_to_current_session
from iai_core_py.entities.annotation_scene_state import AnnotationState
from iai_core_py.entities.datasets import DatasetIdentifier, DatasetPurpose, NullDataset
from iai_core_py.entities.image import Image
from iai_core_py.entities.label import Label
from iai_core_py.entities.media import ImageExtensions, VideoExtensions
from iai_core_py.entities.video import Video
from iai_core_py.entities.video_annotation_statistics import VideoAnnotationStatistics
from iai_core_py.repos import DatasetRepo, VideoRepo
from iai_core_py.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from iai_core_py.repos.storage.storage_client import BytesStream
from iai_core_py.services.dataset_storage_filter_service import DatasetStorageFilterService
from iai_core_py.utils.identifier_factory import IdentifierFactory
from iai_core_py.utils.type_helpers import SequenceOrSet

if TYPE_CHECKING:
    from iai_core_py.utils.annotation_scene_state_helper import AnnotationStatePerTask

DEFAULT_SIZE = 250
DEFAULT_THUMBNAIL_JPG_QUALITY = 85

FILE = "file"
FILENAME = "filename"
HEIGHT = "height"
UPLOAD_INFO = "upload_info"
VIDEO = "video"
IMAGE = "image"
WIDTH = "width"
MEDIA = "media"
MEDIA_COUNT = "media_count"

logger = logging.getLogger(__name__)


class MediaRESTController(metaclass=Singleton):
    """
    This controller is responsible for mapping media items, such as images or videos,
    from and to REST.
    """

    @staticmethod
    def get_image_detail(dataset_storage_identifier: DatasetStorageIdentifier, image_id: ID) -> dict[str, Any]:
        """
        Get metadata information about a specific image

        :param dataset_storage_identifier: Identifier of DS containing the image
        :param image_id: ID of the image to describe
        :return: media REST view
        """
        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)

        image = MediaManager.get_image_by_id(dataset_storage_identifier=dataset_storage_identifier, image_id=image_id)
        annotation_state_per_task_per_media = AnnotationManager.get_media_states_per_task(
            dataset_storage_identifier=dataset_storage_identifier,
            media_identifiers=[image.media_identifier],
            project=project,
        )

        annotation_state_per_task: AnnotationStatePerTask | None = annotation_state_per_task_per_media.get(
            image.media_identifier, None
        )
        return MediaRESTViews.media_to_rest(
            media=image,
            media_identifier=image.media_identifier,
            annotation_state_per_task=annotation_state_per_task,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @staticmethod
    def get_video_detail(dataset_storage_identifier: DatasetStorageIdentifier, video_id: ID) -> dict[str, Any]:
        """
        Get metadata information about a specific video in a project.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video to describe
        :return: media REST view
        """
        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)

        video = MediaManager.get_video_by_id(
            dataset_storage_identifier=dataset_storage_identifier, video_id=ID(video_id)
        )
        annotation_state_per_task_per_media = AnnotationManager.get_media_states_per_task(
            dataset_storage_identifier=dataset_storage_identifier,
            media_identifiers=[video.media_identifier],
            project=project,
        )

        annotation_state_per_task: AnnotationStatePerTask | None = annotation_state_per_task_per_media.get(
            video.media_identifier, None
        )

        video_annotation_stats_by_id = DatasetStorageFilterRepo(
            dataset_storage_identifier
        ).get_video_annotation_statistics_by_ids([video_id])
        video_annotation_stat = video_annotation_stats_by_id.get(video_id, None)
        return MediaRESTViews.media_to_rest(
            media=video,
            media_identifier=video.media_identifier,
            annotation_state_per_task=annotation_state_per_task,
            dataset_storage_identifier=dataset_storage_identifier,
            video_annotation_statistics=video_annotation_stat,
        )

    @staticmethod
    @unified_tracing
    def get_image_thumbnail(
        dataset_storage_identifier: DatasetStorageIdentifier,
        image_id: ID,
    ) -> BinaryIO:
        """
        Return the image thumbnail in BinaryIO format.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the image
        :param image_id: ID of the image
        :return: Image thumbnail in BinaryIO format
        """
        return MediaManager.get_image_thumbnail(
            dataset_storage_identifier=dataset_storage_identifier, image_id=image_id
        )

    @staticmethod
    @unified_tracing
    def get_video_thumbnail(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
    ) -> BinaryIO:
        """
        Get the video thumbnail in BinaryIO format. If the thumbnail does not exist one is generated.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video
        :return: Video thumbnail in BinaryIO format
        """
        return MediaManager.get_video_thumbnail(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
        )

    @staticmethod
    @unified_tracing
    def get_video_thumbnail_stream_location(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
    ) -> Path | str:
        """
        Tries to get the path to the thumbnail video without using the database. If the
        path does not exist it is assumed the thumbnail is missing and one is generated.
        None is returned when thumbnail video is missing. A kafka event will be produced
        to generate the thumbnail video.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video
        :return: Path or presigned S3 URL pointing to the thumbnail in the storage if it exists, else None
        :raises: VideoThumbnailNotFoundException if the video thumbnail does not exist
        """
        thumbnail_binary_filename = Video.thumbnail_video_filename_by_video_id(str(video_id))
        thumbnail_repo = VideoRepo(dataset_storage_identifier).thumbnail_binary_repo

        if thumbnail_repo.exists(filename=thumbnail_binary_filename):
            return thumbnail_repo.get_path_or_presigned_url(filename=thumbnail_binary_filename)

        # Check if a temporary file has already been created
        thumbnail_temp_path = thumbnail_repo.create_path_for_temporary_file(
            filename=thumbnail_binary_filename, make_unique=False
        )
        if not os.path.exists(thumbnail_temp_path):
            video = MediaManager.get_video_by_id(
                dataset_storage_identifier=dataset_storage_identifier,
                video_id=video_id,
            )
            publish_event(
                topic="thumbnail_video_missing",
                body={
                    "video_id": video.id_,
                    "workspace_id": dataset_storage_identifier.workspace_id,
                    "project_id": dataset_storage_identifier.project_id,
                    "dataset_storage_id": dataset_storage_identifier.dataset_storage_id,
                },
                key=str(video.id_).encode(),
                headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
            )
        raise VideoThumbnailNotFoundException(video_id=video_id)

    @staticmethod
    def download_video_frame(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        frame_index: int | None,
    ) -> np.ndarray:
        """
        Retrieve a specific video frame from a given project.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video the frame belongs to
        :param frame_index: Index of the frame to get
        :return: REST representation of the frame in bytes
        """
        return MediaManager.get_video_frame_by_id(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
            frame_index=frame_index,
        )

    @staticmethod
    def download_video_frame_thumbnail(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        frame_index: int | None = None,
    ) -> np.ndarray:
        """
        Retrieve a specific video frame as thumbnail from a given project.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video the frame belongs to
        :param frame_index: Index of the frame to get
        :return: REST representation of the frame thumbnail in bytes
        """
        return MediaManager.get_video_thumbnail_frame_by_id(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
            frame_index=frame_index,
        )

    @staticmethod
    @unified_tracing
    def download_video_stream(dataset_storage_identifier: DatasetStorageIdentifier, video_id: ID) -> Path | str:
        """
        Downloads a video by ID.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video to download
        :return: downloaded video stream data
        """
        return MediaManager.get_path_or_presigned_url_for_video(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
        )

    @staticmethod
    def _parse_and_validate_media_filename(upload_file: UploadFile) -> tuple[str, str]:
        """
        Parse the name of the media file to be uploaded from the request and validate it.

        :param upload_file: File uploaded in the request
        :return: Tuple containing the basename and raw extension of the media file (e.g. ('image', '.jpg'))
        :raises: InvalidMediaException if the filename is invalid
        """
        raw_filename = upload_file.filename
        if raw_filename is None:
            raise InvalidMediaException("Cannot upload media with an unspecified file name")

        filename = raw_filename.strip()
        if not filename:
            raise InvalidMediaException("Cannot upload media with an empty file name")

        basename, extension = os.path.splitext(filename)
        basename = basename.strip()  # remove whitespace characters between the basename and the extension
        if not basename:
            raise InvalidMediaException("Cannot upload media with an empty basename")
        if not extension:
            raise InvalidMediaException("Cannot upload media without an extension")

        return basename, extension

    @staticmethod
    def _resolve_image_extension(raw_extension: str) -> ImageExtensions:
        """
        Resolve the image extension from the raw extension string.

        :param raw_extension: Raw extension of the image (e.g. '.jpg')
        :return: ImageExtensions enum value
        :raises: InvalidMediaException if the extension is not supported
        """
        try:
            return ImageExtensions[raw_extension[1:].upper()]  # remove leading dot and convert to uppercase
        except ValueError:
            raise InvalidMediaException(f"Unsupported image extension: '{raw_extension}'")

    @staticmethod
    def _resolve_video_extension(raw_extension: str) -> VideoExtensions:
        """
        Resolve the video extension from the raw extension string.

        :param raw_extension: Raw extension of the video (e.g. '.mp4')
        :return: VideoExtensions enum value
        :raises: InvalidMediaException if the extension is not supported
        """
        try:
            return VideoExtensions[raw_extension[1:].upper()]  # remove leading dot and convert to uppercase
        except ValueError:
            raise InvalidMediaException(f"Unsupported video extension: '{raw_extension}'")

    @staticmethod
    @unified_tracing
    def upload_media(
        user_id: ID,
        dataset_storage_identifier: DatasetStorageIdentifier,
        media_type: MediaType,
        label_info: dict,
        file_from_request: UploadFile,
    ) -> dict[str, Any]:
        """
        Upload a media entity. Given a file, and upload metadata.

        In the upload request can the following data exist:
         - labels: the media entity will be automatically annotated
             with the assigned labels.
         - filename: The filename of the entity will be overridden with this filename
             but they will be multiple requests).
             This property marks the end. If so, messages will be broadcast.

        :param user_id: ID of the user who uploads the media
        :param dataset_storage_identifier: Identifier of the dataset storage where to upload the media
        :param media_type: type of media: "image" or "video"
        :param label_info: dictionary with labels to apply to uploaded media
        :param file_from_request: FileStorage object from which stream can be read
        :return: dictionary response
        """
        basename, raw_extension = MediaRESTController._parse_and_validate_media_filename(upload_file=file_from_request)

        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)
        check_max_number_of_media_files(project)

        first_task = project.get_trainable_task_nodes()[0]
        labels = MediaRESTController.get_label_from_upload_request(label_info, project.identifier)
        if len(labels) > 0:
            if not first_task.task_properties.is_global and not first_task.task_properties.is_anomaly:
                raise NotImplementedError(
                    "Uploading media with labels to a task that does not support global labels is not allowed."
                )
            # Add extra info to the session to inform other components (e.g. auto-train controller)
            # that the annotation is uploaded together with the media
            add_extra_to_current_session("labeled_media_upload", "True")

        if not file_from_request.size:
            raise RuntimeError("Uploaded file should have size defined")
        data_stream = BytesStream(data=file_from_request.file, length=file_from_request.size)

        media_entity: Video | Image
        update_metrics = ENABLE_METRICS
        if media_type is MediaType.VIDEO:
            video_extension = MediaRESTController._resolve_video_extension(raw_extension)
            media_entity = MediaManager.upload_video(
                dataset_storage_identifier=dataset_storage_identifier,
                basename=basename,
                extension=video_extension,
                data_stream=data_stream,
                user_id=user_id,
                update_metrics=update_metrics,
            )
        elif media_type is MediaType.IMAGE:
            img_extension = MediaRESTController._resolve_image_extension(raw_extension)
            media_entity = MediaManager.upload_image(
                dataset_storage_identifier=dataset_storage_identifier,
                basename=basename,
                extension=img_extension,
                data_stream=data_stream,
                user_id=user_id,
                update_metrics=update_metrics,
            )
        else:
            raise ValueError(
                f"Media uploads with media type {media_type} unsupported. Only image and video uploads are supported."
            )

        DatasetStorageFilterService.on_new_media_upload(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
            media_id=media_entity.id_,
            media_type=media_type,
        )

        publish_event(
            topic="media_uploads",
            body={
                "workspace_id": dataset_storage_identifier.workspace_id,
                "project_id": dataset_storage_identifier.project_id,
                "dataset_storage_id": dataset_storage_identifier.dataset_storage_id,
                "media_id": media_entity.id_,
                "media_type": media_entity.media_identifier.media_type.value,
            },
            key=str(media_entity.id_).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

        video_annotation_stat: VideoAnnotationStatistics | None = None
        annotation_state_per_task: AnnotationStatePerTask
        if len(labels) > 0:
            if isinstance(media_entity, Video):
                annotation_state_per_task = VideoRangeAnnotationManager.create_global_annotations_for_video(
                    project=project,
                    dataset_storage_identifier=dataset_storage_identifier,
                    video=media_entity,
                    user_id=user_id,
                    labels=labels,
                )
                annotated_frames = len(IdentifierFactory.generate_frame_identifiers_for_video(media_entity))
                video_annotation_stat = VideoAnnotationStatistics(
                    annotated=annotated_frames,
                    partially_annotated=0,
                    unannotated=media_entity.total_frames - annotated_frames,
                )
            else:
                annotation_state_per_task = AnnotationManager.create_global_annotations_for_image(
                    project=project,
                    dataset_storage_identifier=dataset_storage_identifier,
                    image=media_entity,
                    user_id=user_id,
                    labels=labels,
                )
        else:
            task_ids = [task.id_ for task in project.get_trainable_task_nodes()]
            annotation_state = AnnotationState.NONE if media_type is MediaType.IMAGE else None
            annotation_state_per_task = dict.fromkeys(task_ids, annotation_state)
            if isinstance(media_entity, Video):
                video_annotation_stat = VideoAnnotationStatistics(
                    annotated=0, partially_annotated=0, unannotated=media_entity.total_frames
                )

        return MediaRESTViews.media_to_rest(
            media=media_entity,
            media_identifier=media_entity.media_identifier,
            annotation_state_per_task=annotation_state_per_task,
            dataset_storage_identifier=dataset_storage_identifier,
            video_annotation_statistics=video_annotation_stat,
        )

    @staticmethod
    def delete_image(
        dataset_storage_identifier: DatasetStorageIdentifier,
        image_id: ID,
    ) -> dict[str, Any]:
        """
        Delete an image by ID from a project.

        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the image to delete
        :param image_id: ID of the image to delete
        :return: success or error REST response
        """
        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)
        dataset_storage = ProjectManager.get_dataset_storage_by_id(
            project=project,
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
        )
        MediaManager.delete_image_by_id(project=project, dataset_storage=dataset_storage, image_id=ID(image_id))

        return success_response_rest()

    @staticmethod
    def get_labels_by_ids(label_ids: SequenceOrSet[ID], project_identifier: ProjectIdentifier) -> list[Label]:
        """
        This function will get a list of labels from a provided list of IDs

        :param label_ids: IDs of requested labels
        :param project_identifier: Identifier of the project to which the labels belong
        :return: The label with id label_id
        :raises: LabelSchemaNotFoundException if no label schema is found,
        """
        project_label_schema = LabelSchemaService.get_latest_label_schema_for_project(project_identifier)
        project_labels = project_label_schema.get_all_labels()
        found_labels = [label for label in project_labels if label.id_ in label_ids]
        found_label_ids = {label.id_ for label in found_labels}
        label_ids_not_found = set(label_ids) - found_label_ids
        if label_ids_not_found:
            raise LabelNotFoundException(
                message=f"Labels with the following IDs were not found in the project: {str(label_ids_not_found)}"
            )
        return [label for label in project_labels if label.id_ in label_ids]  # type: ignore

    @staticmethod
    def delete_video(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
    ) -> dict[str, Any]:
        """
        Delete an video by ID from a project.

        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the video to delete
        :param video_id: ID of the video to delete
        :return: success or error REST response
        """
        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)
        dataset_storage = ProjectManager.get_dataset_storage_by_id(
            project=project,
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
        )
        MediaManager.delete_video_by_id(project=project, dataset_storage=dataset_storage, video_id=ID(video_id))

        return success_response_rest()

    @staticmethod
    def get_label_from_upload_request(upload_info: dict, project_identifier: ProjectIdentifier) -> list[Label]:
        """
        Get the labels of the uploaded media by ID

        :param upload_info: the info containing the label IDs
        :param project_identifier: Identifier of the project where the media is uploaded
        :return: a list of labels which were uploaded with the media
        :raises: MediaUploadedWithNoLabelToAnomalyTaskException if media is uploaded
            without label to an Anomaly task
        """
        labels = []
        if len(upload_info) > 0:
            label_ids = upload_info.get("label_ids", [])
            label_ids = [ID(label_id) for label_id in label_ids]
            if label_ids:
                labels = MediaRESTController.get_labels_by_ids(
                    label_ids=label_ids,
                    project_identifier=project_identifier,
                )
        # TODO CVS-91571 re-enable validation check once SDK supports anomaly workflow
        # first_task_node = project.get_trainable_task_nodes()[0]
        # if not labels and first_task_node.task_properties.is_anomaly:
        #     raise MediaUploadedWithNoLabelToAnomalyTaskException()
        return labels

    @staticmethod
    def get_attr_from_upload_info(request: dict, attribute: str, default: T) -> T:
        """
        Retrieves end of stream flag from upload info.
        Default: True if does not exist.

        :param request:
        :return:
        """
        return json.loads(request.get(UPLOAD_INFO, "{}")).get(attribute, default)

    @staticmethod
    def get_filtered_items(
        dataset_storage_identifier: DatasetStorageIdentifier,
        dataset_filter: DatasetFilter,
        video_id: ID | None = None,
        dataset_id: ID | None = None,
        fps: int | None = None,
        include_frame_details: bool = False,
    ) -> dict:
        """
        Get the media items matching the dataset filter and converts them to a rest
        response

        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the media to filter
        :param dataset_filter: DatasetFilter to match media items against
        :param video_id: Optional ID to use if specifically filtering frames in a video.
            If absent, the entire dataset storage is searched.
        :param dataset_id: ID of a dataset to find media in
        :param fps: number of frames per second to return. Only applicable if video_id is
            not None. If 0, all frames are returned
        :param include_frame_details: bool indicating whether frame details should be included
            in the REST view
        :return: REST view with media results matching the dataset filter
        """
        project = ProjectManager.get_project_by_id(project_id=dataset_storage_identifier.project_id)
        dataset_storage = ProjectManager.get_dataset_storage_by_id(
            project=project,
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
        )

        query_results: QueryResults
        video_frame_indices: list[int] = []
        if dataset_id:
            # If a dataset was specified, verify that it exists and has the 'training' purpose
            dataset = DatasetRepo(dataset_storage_identifier).get_by_id(dataset_id)
            if isinstance(dataset, NullDataset):
                raise TrainingRevisionNotFoundException(dataset_id)
            if dataset.purpose is not DatasetPurpose.TRAINING:
                raise UnexpectedDatasetPurposeException(dataset_id=dataset_id, expected_purpose=DatasetPurpose.TRAINING)
            query_results = QueryBuilder.get_results_for_training_revision_filter(
                dataset_filter=dataset_filter,
                dataset_identifier=DatasetIdentifier.from_ds_identifier(
                    dataset_storage_identifier=dataset_storage.identifier,
                    dataset_id=dataset_id,
                ),
                video_id=video_id,
            )
        elif video_id is None:
            query_results = QueryBuilder.get_media_results_for_dataset_storage_filter(
                dataset_filter=dataset_filter,
                dataset_storage_identifier=dataset_storage.identifier,
            )
        else:
            if fps is None:
                raise ValueError("fps cannot be None for a dataset storage video query")
            video_frame_query_results = QueryBuilder.get_video_frame_results_for_dataset_storage_filter(
                dataset_filter=dataset_filter,
                dataset_storage_identifier=dataset_storage_identifier,
                video_id=video_id,
                fps=fps,
                include_frame_details=include_frame_details,
            )
            query_results = video_frame_query_results.query_results
            video_frame_indices = video_frame_query_results.video_frame_indices

        media_anno_states_per_task = AnnotationManager.get_media_states_per_task(
            project=project,
            dataset_storage_identifier=dataset_storage_identifier,
            media_identifiers=query_results.media_identifiers,
        )
        if dataset_id and video_id is not None:
            return FilteredDatasetRESTView.filtered_dataset_for_video_to_rest(
                dataset_storage_identifier=dataset_storage_identifier,
                query_results=query_results,
                dataset_filter=dataset_filter,
                media_annotation_states_per_task=media_anno_states_per_task,
                dataset_id=dataset_id,
                video_id=video_id,
            )
        if dataset_id is not None:
            return FilteredDatasetRESTView.filtered_dataset_to_rest(
                dataset_storage_identifier=dataset_storage_identifier,
                query_results=query_results,
                dataset_filter=dataset_filter,
                media_annotation_states_per_task=media_anno_states_per_task,
                dataset_id=dataset_id,
            )
        if video_id is None:
            return FilteredDatasetRESTView.filtered_dataset_storage_to_rest(
                dataset_storage_identifier=dataset_storage_identifier,
                query_results=query_results,
                dataset_filter=dataset_filter,
                media_annotation_states_per_task=media_anno_states_per_task,
            )
        video: Video = VideoRepo(dataset_storage_identifier).get_by_id(video_id)
        return FilteredDatasetRESTView.filtered_frames_to_rest(
            dataset_storage_identifier=dataset_storage_identifier,
            video_frame_indices=video_frame_indices,
            query_results=query_results,
            dataset_filter=dataset_filter,
            media_annotation_states_per_task=media_anno_states_per_task,
            video=video,
            include_frame_details=include_frame_details,
        )

    @staticmethod
    def get_project_thumbnail(
        dataset_storage_identifier: DatasetStorageIdentifier,
    ) -> BinaryIO:
        """
        Return thumbnail of oldest image or video

        :param dataset_storage_identifier: Identifier of the dataset storage
        :return: thumbnail BinaryIO content
        """
        thumbnail_media = MediaManager.get_first_media(dataset_storage_identifier)

        if thumbnail_media is None:
            raise NoMediaInProjectException("There is no media available in this project.")

        if isinstance(thumbnail_media, Image):
            return MediaRESTController.get_image_thumbnail(
                dataset_storage_identifier=dataset_storage_identifier,
                image_id=thumbnail_media.id_,
            )
        return MediaRESTController.get_video_thumbnail(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=thumbnail_media.id_,
        )
