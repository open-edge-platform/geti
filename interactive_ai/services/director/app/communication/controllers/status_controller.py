# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the StatusController"""

import logging
from typing import Any

from communication.jobs_client import JobsClient
from communication.views.status_rest_views import StatusRestViews
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper
from features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from service.project_service import ProjectService

from geti_types import ID, DatasetStorageIdentifier
from grpc_interfaces.job_submission.client import CommunicationError
from grpc_interfaces.job_submission.pb.job_service_pb2 import ListJobsResponse
from sc_sdk.repos import BinaryRepo
from sc_sdk.utils.filesystem import MIN_FREE_SPACE_GIB

logger = logging.getLogger(__name__)
FREE_SPACE_WARNING_THRESHOLD = 10000000000  # 10GB in bytes
RUNNING_STATE = "running"


class StatusController:
    @staticmethod
    def get_server_status(user_id: ID) -> dict[str, Any]:
        """
        Returns jsonify REST view of the status of the server.

        Note: currently it only contains the number of running jobs.

        :param user_id: ID of the user requesting the status
        :return: REST dict containing the status information
        """
        jobs_client = JobsClient().jobs_client
        try:
            n_running_jobs = jobs_client.get_count(
                author_uid=user_id,
                state=RUNNING_STATE,
                all_permitted_jobs=True,
            )
        except CommunicationError:
            logger.exception("Error while requesting jobs count from gRPC client.")
            n_running_jobs = 0

        result = {"n_running_jobs": n_running_jobs}

        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_STORAGE_SIZE_COMPUTATION):
            total_space, _, free_space = BinaryRepo.get_disk_stats()
            free_space_gib = free_space / 2**30
            warning = (
                f"Free space is running low - only {round(free_space_gib, 2)} GB left of which "
                f"{MIN_FREE_SPACE_GIB} GB is reserved for the system. "
                if free_space < FREE_SPACE_WARNING_THRESHOLD
                else ""
            )

            result["storage"] = {
                "total_space": total_space,
                "free_space": free_space,
            }
            result["warning"] = warning

        return result

    @staticmethod
    def get_project_status(workspace_id: ID, project_id: ID) -> dict[str, Any]:
        """
        Get a REST view of the status of a project, which contains information on the running jobs, required
         annotations and the performance of the project.

        :param workspace_id: ID of the workspace the project belongs to
        :param project_id: ID of the project to query the status for
        :return: REST view of the status for this project
        """
        project = ProjectService.get_by_id(project_id=project_id)
        training_dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id, project_id=project_id, dataset_storage_id=project.training_dataset_storage_id
        )
        trainable_task_nodes = project.get_trainable_task_nodes()

        missing_annotations_per_task = {
            task_node.id_: MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=training_dataset_storage_identifier,
                task_node=task_node,
            )
            for task_node in trainable_task_nodes
        }
        n_workspace_running_jobs: int
        jobs_page: ListJobsResponse = ListJobsResponse()
        running_jobs = list(jobs_page.jobs)

        load_next_jobs_page: bool = True

        jobs_client = JobsClient().jobs_client
        try:
            n_workspace_running_jobs = jobs_client.get_count(workspace_id=workspace_id, state=RUNNING_STATE)
        except CommunicationError:
            logger.exception("Error while requesting jobs count from gRPC client.")
            n_workspace_running_jobs = 0
            load_next_jobs_page = False

        while load_next_jobs_page:
            jobs_page = jobs_client.find(
                workspace_id=workspace_id,
                project_id=project_id,
                state=RUNNING_STATE,
                limit=jobs_page.next_page.limit if running_jobs else None,
                skip=jobs_page.next_page.skip if running_jobs else None,
                sort_by="priority",
                sort_direction="asc",
            )
            running_jobs += list(jobs_page.jobs)
            load_next_jobs_page = jobs_page.has_next_page

        return StatusRestViews.project_status_to_rest(
            project=project,
            running_jobs=running_jobs,
            missing_annotations_per_task=missing_annotations_per_task,
            n_workspace_running_jobs=n_workspace_running_jobs,
        )

    @staticmethod
    def get_incremental_learning_status(workspace_id: ID, project_id: ID) -> dict:
        """
        For a project, create a MissingAnnotations object describing the number of annotations the user needs to add
        before training will be started.

        :param workspace_id: ID of the workspace the project lives in
        :param project_id: ID of the project to fetch the missing annotations for
        :return: Dictionary containing a MissingAnnotations object for every trainable task in the project
        """
        project = ProjectService.get_by_id(project_id=project_id)
        training_dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=project.training_dataset_storage_id,
        )
        missing_annotations = {
            task_node.id_: MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=training_dataset_storage_identifier,
                task_node=task_node,
            )
            for task_node in project.get_trainable_task_nodes()
        }
        return StatusRestViews.incremental_learning_status_to_rest(missing_annotations)
