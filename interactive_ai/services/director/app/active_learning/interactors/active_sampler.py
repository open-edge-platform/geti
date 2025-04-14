# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the 'sampler' component for Active Learning"""

import logging
import time
from typing import cast

from active_learning.entities import ActiveScoreSuggestionInfo
from active_learning.entities.active_manager import PipelineActiveManager, TaskActiveManager
from active_learning.entities.active_manager.base_active_manager import BaseActiveManager

from geti_telemetry_tools import unified_tracing
from geti_types import ID, MediaIdentifierEntity

logger = logging.getLogger(__name__)


class ActiveSampler:
    """
    The Active Sampler is responsible for returning active sets based on the active
    scores associated to the media at the pipeline and task level.

    The sampler exploits the methods exposed by
    :func:`active_learning.entities.active_manager.TaskActiveManager` and
    :func:`active_learning.entities.active_manager.PipelineActiveManager`
    """

    def __init__(self) -> None:
        raise RuntimeError("The ActiveSampler is static, not meant to be instantiated")

    @staticmethod
    @unified_tracing
    def _get_active_manager(
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        task_node_id: ID | None = None,
    ) -> BaseActiveManager:
        if task_node_id is not None:  # task-level active learning
            return TaskActiveManager(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                task_id=task_node_id,
            )
        # project-level active learning
        return PipelineActiveManager(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )

    @staticmethod
    @unified_tracing
    def _get_suggestions(active_manager: BaseActiveManager, size: int) -> tuple[ActiveScoreSuggestionInfo, ...]:
        active_set_info = active_manager.get_suggestions(size=size)
        # If all the media have been already suggested,
        # reset the suggestions and try again.
        if not active_set_info:
            active_manager.reset_suggestions()
            active_set_info = active_manager.get_suggestions(size=size)
            if not active_set_info:
                # Even after resetting, the mapper could be busy scanning for
                # unannotated media that were never considered before by active
                # learning. In this rare case, try one last time after a few seconds.
                time.sleep(2)
                active_set_info = active_manager.get_suggestions(size=size)
                if not active_set_info:
                    logger.error(
                        "Cannot find media to suggest even after resetting active "
                        "learning for project `%s` in workspace `%s`.",
                        active_manager.project_id,
                        active_manager.workspace_id,
                    )
        return active_set_info

    @staticmethod
    @unified_tracing
    def get_active_set_task_level(
        *,
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        task_id: ID,
        size: int,
        user_id: ID,
    ) -> tuple[MediaIdentifierEntity, ...]:
        """
        Get suggested media (active set) for task-level active learning.

        If all the media have been already presented to the user, the state will
        automatically reset so the same media may be output again.

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project where the task is defined
        :param dataset_storage_id: ID of the dataset storage where the media are stored
        :param task_id: ID of the task node to get suggestions for
        :param size: Max size of the active set [num of media]
        :param user_id: ID of the user requesting the active set
        :return: Identifiers of the media in the active set
        """
        active_manager = ActiveSampler._get_active_manager(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            task_node_id=task_id,
        )
        active_manager = cast("TaskActiveManager", active_manager)

        # Build the active set
        active_set_info = ActiveSampler._get_suggestions(
            active_manager=active_manager,
            size=size,
        )
        media_ids = tuple(info.media_identifier for info in active_set_info)

        if media_ids:
            # Mark the active set items as suggested
            active_manager.mark_as_suggested(
                suggested_media_info=active_set_info,
                user_id=user_id,
                reason=f"Good candidate task-level ({active_manager.task_node_id})",
            )
        else:
            logger.warning(
                "Empty active set for task `%s` of project `%s` in workspace `%s`.",
                task_id,
                project_id,
                workspace_id,
            )

        return media_ids

    @staticmethod
    @unified_tracing
    def get_active_set_project_level(
        *,
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        size: int,
        user_id: ID,
    ) -> tuple[MediaIdentifierEntity, ...]:
        """
        Get suggested media (active set) for project-level active learning.

        If all the media have been already presented to the user, the state will
        automatically reset so the same media may be output again.

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project where the task is defined
        :param dataset_storage_id: ID of the dataset storage where the media are stored
        :param size: Max size of the active set [num of media]
        :param user_id: ID of the user requesting the active set
        :return: Identifiers of the media in the active set
        """
        active_manager = ActiveSampler._get_active_manager(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        active_manager = cast("PipelineActiveManager", active_manager)

        # Build the active set
        active_set_info = ActiveSampler._get_suggestions(
            active_manager=active_manager,
            size=size,
        )
        media_ids = tuple(info.media_identifier for info in active_set_info)

        if media_ids:
            # Mark the active set items as suggested
            active_manager.mark_as_suggested(
                suggested_media_info=active_set_info, user_id=user_id, reason="Good candidate project-level"
            )
        else:
            logger.warning(
                "Empty active set for project `%s` in workspace `%s`.",
                project_id,
                workspace_id,
            )

        return media_ids
