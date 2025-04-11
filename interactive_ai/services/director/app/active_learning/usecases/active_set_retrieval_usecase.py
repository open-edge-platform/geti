# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

"""This module contains the ActiveSetRetrieval use case"""

from active_learning.interactors import ActiveSampler

from geti_telemetry_tools import unified_tracing
from geti_types import ID, MediaIdentifierEntity


class ActiveSetRetrievalUseCase:
    """Use case to get active sets at task or project level."""

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

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project where the task is defined
        :param dataset_storage_id: ID of the dataset storage where the media are stored
        :param task_id: ID of the task node to get suggestions for
        :param size: Max size of the active set [num of media]
        :param user_id: ID of the user requesting the active set
        :return: Identifiers of the media in the active set
        """
        return ActiveSampler.get_active_set_task_level(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            task_id=task_id,
            size=size,
            user_id=user_id,
        )

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

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project where the task is defined
        :param dataset_storage_id: ID of the dataset storage where the media are stored
        :param size: Max size of the active set [num of media]
        :param user_id: ID of the user requesting the active set
        :return: Identifiers of the media in the active set
        """
        return ActiveSampler.get_active_set_project_level(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            size=size,
            user_id=user_id,
        )
