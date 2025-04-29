# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module defines helpers used to check limit constraints"""

import http
import logging

from communication.constants import (
    MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA,
    MAX_NUMBER_OF_MEDIA_PER_PROJECT,
    MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION,
)

from geti_fastapi_tools.exceptions import GetiBaseException
from geti_types import DatasetStorageIdentifier, MediaIdentifierEntity
from sc_sdk.entities.annotation import AnnotationSceneKind
from sc_sdk.entities.project import Project
from sc_sdk.repos import AnnotationSceneRepo, ImageRepo, ProjectRepo, VideoRepo

logger = logging.getLogger(__name__)


class MaxProjectsReachedException(GetiBaseException):
    """
    Exception to indicate the maximum number of projects have been reached
    """

    def __init__(self, maximum: int) -> None:
        super().__init__(
            message=f"You have hit the limit of number of projects in your organization "
            f"({maximum}). Please delete some projects before making new ones.",
            error_code="limit_reached",
            http_status=http.HTTPStatus.CONFLICT,
        )


class MaxMediaFilesReachedException(GetiBaseException):
    """
    Exception to indicate the maximum number of media files have been reached
    """

    def __init__(self, maximum: int) -> None:
        super().__init__(
            message=f"You have hit the limit of number of media ({maximum}). Please delete some before uploading more.",
            error_code="limit_reached",
            http_status=http.HTTPStatus.CONFLICT,
        )


def check_max_number_of_projects(include_hidden: bool = False) -> None:
    """
    Check if the number of projects in the workspace exceeds the maximum allowed

    TODO CVS-130681 - handle project counting across multiple workspaces
    :param include_hidden: Whether to include hidden (not fully created or deleted) projects
    :raises: MaxProjectsReachedException if the maximum number of projects has been hit
    """
    if (
        MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
        and ProjectRepo().count_all(include_hidden=include_hidden) >= MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
    ):
        raise MaxProjectsReachedException(maximum=MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION)


def check_max_number_of_media_files(project: Project) -> None:
    """
    Check if the number of media files in the project exceeds the maximum allowed

    :param project: the project where to look for media
    :raises: MaxProjectsReachedException if the maximum number of projects has been hit
    """
    if MAX_NUMBER_OF_MEDIA_PER_PROJECT:
        total_media_files = 0
        for dataset_storage in project.get_dataset_storages():
            n_all_images = ImageRepo(dataset_storage.identifier).count()
            n_all_videos = VideoRepo(dataset_storage.identifier).count()
            total_media_files += n_all_images + n_all_videos
        if total_media_files >= MAX_NUMBER_OF_MEDIA_PER_PROJECT:
            raise MaxMediaFilesReachedException(maximum=MAX_NUMBER_OF_MEDIA_PER_PROJECT)


def check_max_number_of_annotations_and_delete_extra(
    dataset_storage_identifier: DatasetStorageIdentifier, media_identifier: MediaIdentifierEntity
) -> None:
    """
    Check if the number of annotations for the media has exceeded the maximum allowed, and if it has then delete any
    extra annotation scenes

    :param dataset_storage_identifier: The dataset storage identifier associated with the media to be checked
    :param media_identifier: The media identifier belonging to the annotated media to be checked
    """
    if MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA:
        annotation_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        user_annotations_count = annotation_scene_repo.count_all_by_identifier_and_annotation_kind(
            media_identifier=media_identifier,
            annotation_kind=AnnotationSceneKind.ANNOTATION,
        )
        if user_annotations_count >= MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA:
            n = (user_annotations_count - MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA) + 1
            annotation_scene_repo.delete_n_earliest_annotations_by_identifier_and_annotation_kind(
                media_identifier=media_identifier,
                annotation_kind=AnnotationSceneKind.ANNOTATION,
                n=n,
            )
            logger.warning(
                f"Media ({media_identifier}) has the max number of user annotations, "
                f"the oldest {n} annotation scenes were deleted."
            )
