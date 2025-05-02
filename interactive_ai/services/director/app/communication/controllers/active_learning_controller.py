# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING, Any

from active_learning.usecases import ActiveSetRetrievalUseCase
from communication.exceptions import NoActiveMediaException
from communication.views.active_set_views import ActiveSetRESTViews
from service.project_service import ProjectService

from geti_types import ID, MediaIdentifierEntity, MediaType
from iai_core_py.repos import ImageRepo, VideoRepo
from iai_core_py.utils.annotation_scene_state_helper import AnnotationSceneStateHelper

if TYPE_CHECKING:
    from iai_core_py.entities.image import Image
    from iai_core_py.entities.video import Video


class ActiveLearningController:
    @staticmethod
    def get_active_set(
        workspace_id: ID,
        project_id: ID,
        limit: int,
        user_id: ID,
        task_id: ID | None = None,
    ) -> dict[str, Any]:
        """
        Get a REST view of the active set (project or task level active learning).

        :param workspace_id: ID of the workspace the project belongs to
        :param project_id: ID of the project to get the active set for
        :param limit: Max number of items in the output active set
        :param user_id: ID of the user requesting the active set
        :param task_id: Optional, ID of the task node for per-task active learning.
            If None, active learning will be at full project level.
        :return: REST view of the active set or error response
        """
        project = ProjectService.get_by_id(project_id)
        dataset_storage = project.get_training_dataset_storage()

        if task_id is None:  # project-level active learning
            active_set_media = ActiveSetRetrievalUseCase.get_active_set_project_level(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage.id_,
                size=limit,
                user_id=user_id,
            )
        else:  # task-level active learning
            active_set_media = ActiveSetRetrievalUseCase.get_active_set_task_level(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage.id_,
                task_id=task_id,
                size=limit,
                user_id=user_id,
            )

        if not active_set_media:
            raise NoActiveMediaException

        image_repo = ImageRepo(dataset_storage.identifier)
        video_repo = VideoRepo(dataset_storage.identifier)
        active_set_media_entities: dict[MediaIdentifierEntity, Image | Video] = {
            media_identifier: (
                image_repo.get_by_id(media_identifier.media_id)
                if media_identifier.media_type is MediaType.IMAGE
                else video_repo.get_by_id(media_identifier.media_id)
            )
            for media_identifier in active_set_media
        }

        annotation_scene_states = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
            media_identifiers=active_set_media,
            dataset_storage_identifier=dataset_storage.identifier,
            project=project,
        )
        active_set_rest = ActiveSetRESTViews.active_set_to_rest(
            dataset_storage_identifier=dataset_storage.identifier,
            media_entities_data=active_set_media_entities,
            annotation_scene_states=annotation_scene_states,
        )
        return {"active_set": active_set_rest}
