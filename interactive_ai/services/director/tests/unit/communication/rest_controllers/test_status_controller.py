# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from os import environ
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.controllers.status_controller import FREE_SPACE_WARNING_THRESHOLD, RUNNING_STATE, StatusController
from communication.views.status_rest_views import StatusRestViews
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper
from service.project_service import ProjectService

from geti_types import ID
from grpc_interfaces.job_submission.client import CommunicationError
from grpc_interfaces.job_submission.pb.job_service_pb2 import JobResponse, ListJobsResponse
from iai_core.repos import BinaryRepo, ProjectRepo
from iai_core.utils.filesystem import MIN_FREE_SPACE_GIB

DUMMY_USER = ID("dummy_user")


@pytest.fixture
def fxt_server_status_rest():
    return {
        "n_running_jobs": 1,
        "warning": f"Free space is running low - only {round((FREE_SPACE_WARNING_THRESHOLD - 1.0) / 2**30, 2)} GB left "
        f"of which {MIN_FREE_SPACE_GIB} GB is reserved for the system. ",
        "storage": {
            "free_space": FREE_SPACE_WARNING_THRESHOLD - 1.0,
            "total_space": 100_000_000_000,
        },
    }


class TestStatusController:
    def test_get_missing_annotations_per_task(
        self,
        fxt_project,
        fxt_missing_annotations,
    ) -> None:
        task_node = fxt_project.get_trainable_task_nodes()[0]
        with (
            patch.object(ProjectService, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                MissingAnnotationsHelper,
                "get_missing_annotations_for_task",
                return_value=fxt_missing_annotations,
            ) as mock_get_missing_annotations,
        ):
            result = StatusController.get_incremental_learning_status(
                workspace_id=fxt_project.workspace_id, project_id=fxt_project.id_
            )

            mock_get_project.assert_called_once_with(project_id=fxt_project.id_)
            mock_get_missing_annotations.assert_called_once_with(
                dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
                task_node=task_node,
            )
            assert result == StatusRestViews.incremental_learning_status_to_rest(
                {task_node.id_: fxt_missing_annotations}
            )

    @patch.dict(environ, {"FEATURE_FLAG_STORAGE_SIZE_COMPUTATION": "true"})
    def test_get_server_status(self, fxt_server_status_rest, fxt_mock_jobs_client) -> None:
        num_running_jobs = 1

        fxt_mock_jobs_client._jobs_client.get_count.return_value = num_running_jobs
        with patch.object(
            BinaryRepo,
            "get_disk_stats",
            return_value=(
                100_000_000_000,
                50_000_000_000,
                FREE_SPACE_WARNING_THRESHOLD - 1.0,
            ),
        ) as mock_get_free_space:
            result = StatusController.get_server_status(user_id=ID("dummy_user"))

            compare(result, fxt_server_status_rest, ignore_eq=True)
            fxt_mock_jobs_client._jobs_client.get_count.assert_called_once_with(
                author_uid=ID("dummy_user"),
                state=RUNNING_STATE,
                all_permitted_jobs=True,
            )
            mock_get_free_space.assert_called_once()

    @patch.dict(environ, {"FEATURE_FLAG_STORAGE_SIZE_COMPUTATION": "false"})
    def test_get_server_status_no_storage(self, fxt_mock_jobs_client) -> None:
        num_running_jobs = 1

        fxt_mock_jobs_client._jobs_client.get_count.return_value = num_running_jobs

        result = StatusController.get_server_status(user_id=ID("dummy_user"))

        fxt_mock_jobs_client._jobs_client.get_count.assert_called_once_with(
            author_uid=ID("dummy_user"),
            state=RUNNING_STATE,
            all_permitted_jobs=True,
        )

        assert len(result) == 1
        assert result["n_running_jobs"] == num_running_jobs

    @patch.dict(environ, {"FEATURE_FLAG_STORAGE_SIZE_COMPUTATION": "true"})
    def test_get_server_status_job_client_error(self, fxt_server_status_rest, fxt_mock_jobs_client) -> None:
        """Test that when job MS is not reachable, status will not return an error"""
        fxt_mock_jobs_client._jobs_client.get_count.side_effect = CommunicationError()
        fxt_server_status_rest["n_running_jobs"] = 0
        with (
            patch.object(
                BinaryRepo,
                "get_disk_stats",
                return_value=(
                    100_000_000_000,
                    50_000_000_000,
                    FREE_SPACE_WARNING_THRESHOLD - 1.0,
                ),
            ) as mock_get_free_space,
        ):
            result = StatusController.get_server_status(user_id=ID("dummy_user"))
            compare(result, fxt_server_status_rest, ignore_eq=True)
            mock_get_free_space.assert_called_once()

    def test_get_project_status(self, fxt_project, fxt_missing_annotations, fxt_mock_jobs_client) -> None:
        dataset_storage = fxt_project.get_training_dataset_storage()
        task_node = fxt_project.get_trainable_task_nodes()[0]
        grpc_find_response = ListJobsResponse(
            jobs=[JobResponse()],
            total_count=1,
            has_next_page=False,
        )
        fxt_mock_jobs_client._jobs_client.find.return_value = grpc_find_response
        fxt_mock_jobs_client._jobs_client.get_count.return_value = 1
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                MissingAnnotationsHelper,
                "get_missing_annotations_for_task",
                return_value=fxt_missing_annotations,
            ) as mock_get_missing_annotations,
            patch.object(
                StatusRestViews, "project_status_to_rest", return_value={"mock": "mock"}
            ) as mock_status_to_rest,
        ):
            project_status = StatusController.get_project_status(
                workspace_id=fxt_project.workspace_id, project_id=fxt_project.id_
            )
            mock_get_project.assert_called_once_with(fxt_project.id_)
            mock_get_missing_annotations.assert_called_once_with(
                dataset_storage_identifier=dataset_storage.identifier,
                task_node=task_node,
            )
            fxt_mock_jobs_client._jobs_client.find.assert_called_once_with(
                workspace_id=fxt_project.workspace_id,
                project_id=fxt_project.id_,
                state=RUNNING_STATE,
                sort_by="priority",
                sort_direction="asc",
                limit=None,
                skip=None,
            )
            fxt_mock_jobs_client._jobs_client.get_count.assert_called_once_with(
                workspace_id=fxt_project.workspace_id, state=RUNNING_STATE
            )
            mock_status_to_rest.assert_called_once_with(
                project=fxt_project,
                missing_annotations_per_task={task_node.id_: fxt_missing_annotations},
                running_jobs=list(grpc_find_response.jobs),
                n_workspace_running_jobs=1,
            )
            assert project_status == {"mock": "mock"}

    def test_get_project_status_job_client_error(
        self, fxt_project, fxt_missing_annotations, fxt_mock_jobs_client
    ) -> None:
        """Test that when job MS is not reachable, project status will not return an error"""
        fxt_mock_jobs_client._jobs_client.get_count.side_effect = CommunicationError()
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(
                MissingAnnotationsHelper,
                "get_missing_annotations_for_task",
                return_value=fxt_missing_annotations,
            ),
        ):
            project_status = StatusController.get_project_status(
                workspace_id=fxt_project.workspace_id, project_id=fxt_project.id_
            )
            assert project_status["n_running_jobs"] == 0
            assert project_status["n_running_jobs_project"] == 0
