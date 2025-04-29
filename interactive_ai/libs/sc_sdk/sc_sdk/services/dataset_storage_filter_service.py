# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging

from sc_sdk.entities.dataset_storage_filter_data import DatasetStorageFilterData
from sc_sdk.entities.image import Image
from sc_sdk.entities.media import MediaPreprocessingStatus
from sc_sdk.entities.video import Video
from sc_sdk.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, ImageRepo, VideoRepo
from sc_sdk.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo

from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, MediaType

logger = logging.getLogger(__name__)


class DatasetStorageFilterService:
    @staticmethod
    def on_new_media_upload(
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        media_id: ID,
        media_type: MediaType,
    ) -> None:
        """
        Create a new entry for a media in the dataset storage filter repo

        :param workspace_id: ID of the workspace the project belongs to
        :param project_id: ID of the project to which the media belongs to
        :param dataset_storage_id: ID of the dataset storage to which the media belongs to
        :param media_id: ID of the newly uploaded media
        :param media_type: type of the media (image or video)
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id, project_id=project_id, dataset_storage_id=dataset_storage_id
        )
        media: Image | Video
        match media_type:
            case MediaType.IMAGE:
                media = ImageRepo(dataset_storage_identifier).get_by_id(id_=media_id)
            case MediaType.VIDEO:
                media = VideoRepo(dataset_storage_identifier).get_by_id(id_=media_id)
            case _:
                raise ValueError(
                    f"Cannot handle new media uploads with media type {media_type.name}. "
                    f"The media type should be an image or a video."
                )

        dataset_storage_filter_data = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=media.media_identifier,
            media=media,
            preprocessing=media.preprocessing.status,
        )

        logger.info(
            "Creating dataset storage filter data for newly uploaded media. Project ID: %s, Media ID: %s.",
            project_id,
            media_id,
        )

        dataset_storage_filter_repo = DatasetStorageFilterRepo(dataset_storage_identifier=dataset_storage_identifier)
        dataset_storage_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data)

    @staticmethod
    def on_new_annotation_scene(
        project_id: ID,
        dataset_storage_id: ID,
        annotation_scene_id: ID,
    ) -> None:
        """
        Update an entry for a media with new annotation scene data in the dataset storage filter repo

        :param project_id: ID of the project to which the media belongs to
        :param dataset_storage_id: ID of the dataset storage to which the media belongs to
        :param annotation_scene_id: ID of the newly uploaded annotation scene
        """
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )

        annotation_repo = AnnotationSceneRepo(dataset_storage_identifier=dataset_storage_identifier)
        annotation_scene = annotation_repo.get_by_id(id_=annotation_scene_id)

        annotation_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier=dataset_storage_identifier)
        annotation_state = annotation_state_repo.get_latest_for_annotation_scene(
            annotation_scene_id=annotation_scene_id
        )

        logger.info(
            "Updating dataset storage filter data for newly uploaded annotation scene. "
            "Project ID: %s, "
            "Media Identifier: %s, "
            "Annotation Scene ID: %s.",
            project_id,
            annotation_scene.media_identifier,
            annotation_scene_id,
        )

        video: Video | None = None
        if annotation_scene.media_identifier.media_type is MediaType.VIDEO_FRAME:
            # Video frames are not uploaded separately, so we have to add media filter data
            # together with the annotation scene filter data
            video_repo = VideoRepo(dataset_storage_identifier=dataset_storage_identifier)
            video = video_repo.get_by_id(annotation_scene.media_identifier.media_id)

        dataset_storage_filter_data = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=annotation_scene.media_identifier,
            media=video,
            annotation_scene=annotation_scene,
            media_annotation_state=annotation_state.get_state_media_level(),
            # When new annotation scene event is triggered for video, it should already be preprocessed
            preprocessing=video.preprocessing.status if video is not None else MediaPreprocessingStatus.FINISHED,
        )

        dataset_storage_filter_repo = DatasetStorageFilterRepo(dataset_storage_identifier=dataset_storage_identifier)
        dataset_storage_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data)
