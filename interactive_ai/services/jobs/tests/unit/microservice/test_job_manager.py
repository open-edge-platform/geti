# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from datetime import timedelta
from unittest.mock import ANY, MagicMock, patch

import pytest

from microservice.exceptions import DuplicateJobFoundException, JobNotCancellableException
from microservice.job_manager import JobManager, JobsAcl, JobSortingField, Pagination, SortDirection, TimestampFilter
from microservice.job_repo import SessionBasedMicroserviceJobRepo, WorkspaceBasedMicroserviceJobRepo
from model.duplicate_policy import DuplicatePolicy
from model.job import JobCancellationInfo
from model.job_state import JobState, JobStateGroup
from model.telemetry import Telemetry

from geti_spicedb_tools import SpiceDB, SpiceDBResourceTypes
from geti_types import ID
from sc_sdk.utils.constants import DEFAULT_USER_NAME
from sc_sdk.utils.time_utils import now

DUMMY_JOB_KEY = json.dumps({"job_key": "value"})
project_id = ID("234567890123456789010000")
author = ID("test_uid")


def mock_job_manager(self, *args, **kwargs) -> None:
    self._client = MagicMock()


def mock_job_repo(self, *args, **kwargs) -> None:
    WorkspaceBasedMicroserviceJobRepo._mongo_client = MagicMock()  # type: ignore


def mock_job_repo_2(self, *args, **kwargs) -> None:
    SessionBasedMicroserviceJobRepo._mongo_client = MagicMock()  # type: ignore


def reset_singletons() -> None:
    JobManager._instance = None


@patch.object(SpiceDB, "create_job")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "insert_document", return_value="job_id")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "update_many")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_submit_no_project(
    mock_repo_update_many,
    mock_repo_insert_document,
    request,
    fxt_session_ctx,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    duplicate_policy = DuplicatePolicy.REPLACE

    # Act
    key = json.dumps({"job_key": "value"})
    job_id = JobManager().submit(
        job_type="train",
        priority=2,
        job_name="Train job",
        key=key,
        payload={"workspace_id": str(fxt_session_ctx.workspace_id)},
        metadata={"project_name": "test_project"},
        author=author,
        duplicate_policy=duplicate_policy,
        telemetry=Telemetry(),
        cancellable=True,
    )

    # Assert
    assert job_id == ID("job_id")
    mock_repo_update_many.assert_called_once_with(
        job_filter={"key": key, "state": 0},
        update={
            "$set": {
                "cancellation_info.is_cancelled": True,
                "cancellation_info.delete_job": True,
            }
        },
        mongodb_session=ANY,
    )
    mock_repo_insert_document.assert_called_once_with(
        {
            "workspace_id": str(fxt_session_ctx.workspace_id),
            "type": "train",
            "priority": 2,
            "job_name": "Train job",
            "state": 0,
            "state_group": "SCHEDULED",
            "cancellation_info": {
                "is_cancelled": False,
                "cancellable": True,
            },
            "step_details": [],
            "key": DUMMY_JOB_KEY,
            "payload": {"workspace_id": str(fxt_session_ctx.workspace_id)},
            "metadata": {"project_name": "test_project"},
            "creation_time": ANY,
            "author": author,
            "executions": {"main": {}},
            "session": {
                "organization_id": str(fxt_session_ctx.organization_id),
                "workspace_id": str(fxt_session_ctx.workspace_id),
                "source": "internal",
            },
            "telemetry": {"context": ""},
        },
        mongodb_session=ANY,
    )


@patch.object(SpiceDB, "create_job")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "insert_document", return_value="job_id")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "update_many")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_submit_replace(
    mock_repo_update_many,
    mock_repo_insert_document,
    mock_create_project_job,
    request,
    fxt_session_ctx,
) -> None:
    request.addfinalizer(reset_singletons)

    # Act
    job_id = JobManager().submit(
        job_type="train",
        priority=2,
        job_name="Train job",
        key=DUMMY_JOB_KEY,
        payload={"workspace_id": str(fxt_session_ctx.workspace_id)},
        metadata={"project_name": "test_project"},
        author=author,
        duplicate_policy=DuplicatePolicy.REPLACE,
        telemetry=Telemetry(),
        project_id=project_id,
        cancellable=True,
    )

    # Assert
    mock_repo_update_many.assert_called_once_with(
        job_filter={"key": DUMMY_JOB_KEY, "state": 0},
        update={
            "$set": {
                "cancellation_info.is_cancelled": True,
                "cancellation_info.delete_job": True,
            }
        },
        mongodb_session=ANY,
    )
    mock_repo_insert_document.assert_called_once_with(
        {
            "workspace_id": str(fxt_session_ctx.workspace_id),
            "type": "train",
            "priority": 2,
            "job_name": "Train job",
            "state": 0,
            "state_group": "SCHEDULED",
            "cancellation_info": {
                "is_cancelled": False,
                "cancellable": True,
            },
            "step_details": [],
            "key": DUMMY_JOB_KEY,
            "payload": {"workspace_id": str(fxt_session_ctx.workspace_id)},
            "metadata": {"project_name": "test_project"},
            "creation_time": ANY,
            "author": author,
            "project_id": str(project_id),
            "executions": {"main": {}},
            "session": {
                "organization_id": str(fxt_session_ctx.organization_id),
                "workspace_id": str(fxt_session_ctx.workspace_id),
                "source": "internal",
            },
            "telemetry": {"context": ""},
        },
        mongodb_session=ANY,
    )
    assert job_id == ID("job_id")
    mock_create_project_job.assert_called_once_with(
        job_id="job_id", parent_entity_type=SpiceDBResourceTypes.PROJECT.value, parent_entity_id=str(project_id)
    )


@patch.object(SpiceDB, "create_job")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "preliminary_query_match_filter", return_value={})
@patch.object(WorkspaceBasedMicroserviceJobRepo, "find_one", return_value={"_id": DUMMY_JOB_KEY})
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_submit_omit(
    mock_find_one,
    mock_get_preliminary_query,
    mock_create_project_job,
    request,
    fxt_session_ctx,
) -> None:
    request.addfinalizer(reset_singletons)

    # Act
    job_id = JobManager().submit(
        job_type="train",
        priority=2,
        job_name="Train job",
        key=DUMMY_JOB_KEY,
        payload={"workspace_id": str(fxt_session_ctx.workspace_id)},
        metadata={"project_name": "test_project"},
        author=author,
        duplicate_policy=DuplicatePolicy.OMIT,
        telemetry=Telemetry(),
        project_id=project_id,
        cancellable=True,
    )

    # Assert
    mock_find_one.assert_called_once_with(
        job_filter={
            "key": DUMMY_JOB_KEY,
            "state": {"$lt": JobState.RUNNING.value},
        },
        mongodb_session=ANY,
    )
    assert job_id == DUMMY_JOB_KEY
    mock_get_preliminary_query.assert_not_called()
    mock_create_project_job.assert_not_called()


@patch.object(SpiceDB, "create_job")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "preliminary_query_match_filter", return_value={})
@patch.object(WorkspaceBasedMicroserviceJobRepo, "find_one", return_value={"id": DUMMY_JOB_KEY})
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_submit_reject(
    mock_find_one,
    mock_get_preliminary_query,
    mock_create_project_job,
    request,
    fxt_session_ctx,
) -> None:
    request.addfinalizer(reset_singletons)

    # Act
    with pytest.raises(DuplicateJobFoundException):
        JobManager().submit(
            job_type="train",
            priority=2,
            job_name="Train job",
            key=DUMMY_JOB_KEY,
            payload={"workspace_id": str(fxt_session_ctx.workspace_id)},
            metadata={"project_name": "test_project"},
            author=author,
            duplicate_policy=DuplicatePolicy.REJECT,
            telemetry=Telemetry(),
            project_id=project_id,
            cancellable=True,
        )

    # Assert
    mock_find_one.assert_called_once_with(
        job_filter={
            "key": DUMMY_JOB_KEY,
            "state": {"$lt": JobState.RUNNING.value},
        },
        mongodb_session=ANY,
    )
    mock_get_preliminary_query.assert_not_called()
    mock_create_project_job.assert_not_called()


@patch.object(SpiceDB, "create_job")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "insert_document", return_value="job_id")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "update_many")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
@patch("microservice.job_manager.CreditSystemClient", autospec=True)
def test_submit_cost_requests(
    mock_credits_service_client,
    mock_repo_update_many,
    mock_repo_insert_document,
    mock_create_project_job,
    request,
    fxt_session_ctx,
) -> None:
    request.addfinalizer(reset_singletons)

    client = MagicMock()
    mock_credits_service_client.return_value = client
    client.__enter__.return_value = client
    client.acquire_lease.return_value = "lease_id"

    # Act
    job_id = JobManager().submit(
        job_type="train",
        priority=2,
        job_name="Train job",
        key=DUMMY_JOB_KEY,
        payload={"workspace_id": str(fxt_session_ctx.workspace_id)},
        metadata={"project_name": "test_project"},
        author=author,
        duplicate_policy=DuplicatePolicy.REPLACE,
        telemetry=Telemetry(),
        project_id=project_id,
        cost_requests={"images": 100},
        cancellable=True,
    )

    # Assert
    mock_repo_update_many.assert_called_once_with(
        job_filter={"key": DUMMY_JOB_KEY, "state": 0},
        update={
            "$set": {
                "cancellation_info.is_cancelled": True,
                "cancellation_info.delete_job": True,
            }
        },
        mongodb_session=ANY,
    )
    mock_repo_insert_document.assert_called_once_with(
        {
            "workspace_id": str(fxt_session_ctx.workspace_id),
            "type": "train",
            "priority": 2,
            "job_name": "Train job",
            "state": 0,
            "state_group": "SCHEDULED",
            "cancellation_info": {
                "is_cancelled": False,
                "cancellable": True,
            },
            "step_details": [],
            "key": DUMMY_JOB_KEY,
            "payload": {"workspace_id": str(fxt_session_ctx.workspace_id)},
            "metadata": {"project_name": "test_project"},
            "creation_time": ANY,
            "author": author,
            "project_id": str(project_id),
            "executions": {"main": {}},
            "session": {
                "organization_id": str(fxt_session_ctx.organization_id),
                "workspace_id": str(fxt_session_ctx.workspace_id),
                "source": "internal",
            },
            "telemetry": {"context": ""},
            "cost": {
                "lease_id": "lease_id",
                "requests": [{"amount": 100, "unit": "images"}],
                "consumed": [],
                "reported": False,
            },
        },
        mongodb_session=ANY,
    )
    assert job_id == ID("job_id")
    mock_create_project_job.assert_called_once_with(
        job_id="job_id", parent_entity_type=SpiceDBResourceTypes.PROJECT.value, parent_entity_id=str(project_id)
    )


@patch("microservice.job_manager.JobMapper.backward")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "get_document_by_id")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_get_by_id_none(
    mock_repo_get_by_id,
    mock_mapper_backward,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")

    mock_repo_get_by_id.return_value = None

    # Act
    returned_job = JobManager().get_by_id(job_id=job_id)

    # Assert
    assert returned_job is None
    mock_repo_get_by_id.assert_called_once_with(job_id)
    mock_mapper_backward.assert_not_called()


@patch("microservice.job_manager.JobMapper.backward")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "get_document_by_id")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_get_by_id(
    mock_repo_get_by_id,
    mock_mapper_backward,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    job_dict = {"_id": "job_id"}
    job: dict = {}

    mock_repo_get_by_id.return_value = job_dict
    mock_mapper_backward.return_value = job

    # Act
    returned_job = JobManager().get_by_id(job_id=job_id)

    # Assert
    assert returned_job == job
    mock_repo_get_by_id.assert_called_once_with(job_id)
    mock_mapper_backward.assert_called_once_with(job_dict)


@patch.object(WorkspaceBasedMicroserviceJobRepo, "update")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "get_by_id")
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_mark_cancelled_job_not_found(mock_jm_get_by_id, mock_repo_update, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    mock_jm_get_by_id.return_value = None

    # Act
    cancelled = JobManager().mark_cancelled(job_id=job_id, user_uid=DEFAULT_USER_NAME)

    # Assert
    mock_repo_update.assert_not_called()
    assert not cancelled


@pytest.mark.parametrize("state", JobState)
@pytest.mark.parametrize("cancellable", [True, False])
@patch.object(WorkspaceBasedMicroserviceJobRepo, "update")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "get_by_id")
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_mark_cancelled(mock_jm_get_by_id, mock_repo_update, request, state, cancellable) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_id = ID("job_id")
    job = MagicMock()
    job.state = state
    job.cancellation_info = JobCancellationInfo(cancellable=cancellable)
    mock_jm_get_by_id.return_value = job

    # Act
    exception = None
    try:
        JobManager().mark_cancelled(job_id=job_id, user_uid=DEFAULT_USER_NAME)
    except JobNotCancellableException as ex:
        exception = ex

    # Assert
    if JobState.READY_FOR_SCHEDULING.value < state.value < JobState.FINISHED.value and not cancellable:
        mock_repo_update.assert_not_called()
        assert exception is not None
    else:
        mock_repo_update.assert_called_once_with(
            job_id=job_id,
            update={
                "$set": {
                    "cancellation_info.delete_job": False,
                    "cancellation_info.is_cancelled": True,
                    "cancellation_info.request_time": ANY,
                    "cancellation_info.user_uid": DEFAULT_USER_NAME,
                }
            },
        )


@patch.object(SessionBasedMicroserviceJobRepo, "count")
@patch.object(SessionBasedMicroserviceJobRepo, "__init__", new=mock_job_repo_2)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_get_jobs_count_all(mock_repo_count, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_repo_count.return_value = 20

    # Act
    count = JobManager().get_jobs_count()

    # Assert
    assert count == 20
    mock_repo_count.assert_called_once_with({})


@patch.object(SessionBasedMicroserviceJobRepo, "count")
@patch.object(SessionBasedMicroserviceJobRepo, "__init__", new=mock_job_repo_2)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_get_jobs_count_filter(mock_repo_count, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    from_val = now() - timedelta(minutes=20)
    to_val = now() - timedelta(minutes=10)
    mock_repo_count.return_value = 20
    acl = JobsAcl(permitted_projects=[project_id], workspace_jobs_author="author_uid")

    # Act
    count = JobManager().get_jobs_count(
        job_types=["train"],
        state_group=JobStateGroup.SCHEDULED,
        project_id=project_id,
        key=DUMMY_JOB_KEY,
        author_uid="author_uid",
        start_time=TimestampFilter(from_val=from_val, to_val=to_val),
        acl=acl,
    )

    # Assert
    assert count == 20
    mock_repo_count.assert_called_once_with(
        {
            "type": {"$in": ["train"]},
            "state_group": "SCHEDULED",
            "key": DUMMY_JOB_KEY,
            "author": "author_uid",
            "start_time": {"$gte": from_val, "$lte": to_val},
            "project_id": str(project_id),
            "$or": [{"project_id": {"$in": [project_id]}}, {"project_id": {"$exists": False}, "author": "author_uid"}],
        }
    )


@patch.object(WorkspaceBasedMicroserviceJobRepo, "aggregate_read")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_find_all_none_found(mock_repo_aggregate, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_repo_aggregate.return_value = []

    # Act
    jobs = JobManager().find()

    # Assert
    assert jobs == ()
    mock_repo_aggregate.assert_called_once_with([{"$match": {}}, {"$sort": {"_id": 1}}])


@patch("microservice.job_manager.JobMapper.backward")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "aggregate_read")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_find_all_found(
    mock_repo_aggregate,
    mock_mapper_backward,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job_dict = {"_id": "job_id"}
    job: dict = {}
    mock_repo_aggregate.return_value = [job_dict]
    mock_mapper_backward.return_value = job

    # Act
    jobs = JobManager().find()

    # Assert
    assert jobs == (job,)
    mock_repo_aggregate.assert_called_once_with([{"$match": {}}, {"$sort": {"_id": 1}}])
    mock_mapper_backward.assert_called_once_with(job_dict)


@patch.object(WorkspaceBasedMicroserviceJobRepo, "aggregate_read")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_find_filtered(mock_repo_aggregate, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    from_val = now() - timedelta(minutes=20)
    to_val = now() - timedelta(minutes=10)

    mock_repo_aggregate.return_value = []

    acl = JobsAcl(permitted_projects=[project_id], workspace_jobs_author="author_uid")

    # Act
    jobs = JobManager().find(
        job_types=["train"],
        state_group=JobStateGroup.SCHEDULED,
        project_id=project_id,
        key=DUMMY_JOB_KEY,
        author_uid="author_uid",
        start_time=TimestampFilter(from_val=from_val, to_val=to_val),
        acl=acl,
    )

    # Assert
    assert jobs == ()
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "type": {"$in": ["train"]},
                    "state_group": "SCHEDULED",
                    "project_id": str(project_id),
                    "key": DUMMY_JOB_KEY,
                    "author": "author_uid",
                    "start_time": {"$gte": from_val, "$lte": to_val},
                    "$or": [
                        {"project_id": {"$in": [project_id]}},
                        {"project_id": {"$exists": False}, "author": "author_uid"},
                    ],
                }
            },
            {"$sort": {"_id": 1}},
        ]
    )


@patch.object(WorkspaceBasedMicroserviceJobRepo, "aggregate_read")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_find_filtered_states(mock_repo_aggregate, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    from_val = now() - timedelta(minutes=20)
    to_val = now() - timedelta(minutes=10)

    mock_repo_aggregate.return_value = []

    # Act
    jobs = JobManager().find(
        job_types=["train"],
        states=[JobState.SUBMITTED, JobState.RUNNING],
        project_id=project_id,
        key=DUMMY_JOB_KEY,
        author_uid="author_uid",
        start_time=TimestampFilter(from_val=from_val, to_val=to_val),
    )

    # Assert
    assert jobs == ()
    mock_repo_aggregate.assert_called_once_with(
        [
            {
                "$match": {
                    "type": {"$in": ["train"]},
                    "state": {"$in": [0, 4]},
                    "project_id": str(project_id),
                    "key": DUMMY_JOB_KEY,
                    "author": "author_uid",
                    "start_time": {"$gte": from_val, "$lte": to_val},
                }
            },
            {"$sort": {"_id": 1}},
        ]
    )


@patch.object(WorkspaceBasedMicroserviceJobRepo, "aggregate_read")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_find_pagination(mock_repo_aggregate, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_repo_aggregate.return_value = []

    # Act
    jobs = JobManager().find(pagination=Pagination(skip=5, limit=10))

    # Assert
    assert jobs == ()
    mock_repo_aggregate.assert_called_once_with(
        [
            {"$match": {}},
            {"$sort": {"_id": 1}},
            {"$skip": 5},
            {"$limit": 10},
        ]
    )


@patch.object(WorkspaceBasedMicroserviceJobRepo, "aggregate_read")
@patch.object(WorkspaceBasedMicroserviceJobRepo, "__init__", new=mock_job_repo)
@patch.object(JobManager, "__init__", new=mock_job_manager)
def test_find_sorting(mock_repo_aggregate, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_repo_aggregate.return_value = []

    # Act
    jobs = JobManager().find(
        sort_by=JobSortingField.START_TIME,
        sort_direction=SortDirection.DESC,
    )

    # Assert
    assert jobs == ()
    mock_repo_aggregate.assert_called_once_with([{"$match": {}}, {"$sort": {"_id": -1, "start_time": -1}}])


def test_normalize_key() -> None:
    key = json.dumps({"b": "a", "a": "d", "c": "c"})
    expected_normalized_key = json.dumps({"a": "d", "b": "a", "c": "c"})
    normalized_key = JobManager._normalize_key(key)
    assert normalized_key == expected_normalized_key


def test_get_acl_filter_empty() -> None:
    # Arrange
    acl = JobsAcl()

    # Act
    acl_filter = JobManager()._get_acl_filter(acl=acl)

    # Assert
    assert acl_filter == {"$or": [{"project_id": {"$exists": True}}, {"project_id": {"$exists": False}}]}


def test_get_acl_filter_permitted_projects() -> None:
    # Arrange
    acl = JobsAcl(permitted_projects=[project_id])

    # Act
    acl_filter = JobManager()._get_acl_filter(acl=acl)

    # Assert
    assert acl_filter == {"$or": [{"project_id": {"$in": [project_id]}}, {"project_id": {"$exists": False}}]}


def test_get_acl_filter_workspace_jobs_author() -> None:
    # Arrange
    acl = JobsAcl(workspace_jobs_author="author_id")

    # Act
    acl_filter = JobManager()._get_acl_filter(acl=acl)

    # Assert
    assert acl_filter == {
        "$or": [{"project_id": {"$exists": True}}, {"project_id": {"$exists": False}, "author": "author_id"}]
    }


def test_get_acl_filter_workspace_full() -> None:
    # Arrange
    acl = JobsAcl(permitted_projects=[project_id], workspace_jobs_author="author_id")

    # Act
    acl_filter = JobManager()._get_acl_filter(acl=acl)

    # Assert
    assert acl_filter == {
        "$or": [{"project_id": {"$in": [project_id]}}, {"project_id": {"$exists": False}, "author": "author_id"}]
    }
