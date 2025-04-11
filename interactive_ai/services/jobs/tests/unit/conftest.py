# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import json
import logging

import pytest
from bson import ObjectId

from model.job import (
    Job,
    JobCancellationInfo,
    JobConsumedResource,
    JobCost,
    JobFlyteExecutions,
    JobMainFlyteExecution,
    JobResource,
    JobStepDetails,
)
from model.job_state import JobState, JobStateGroup, JobTaskState
from model.telemetry import Telemetry

from geti_types import ID, RequestSource, make_session, session_context
from grpc_interfaces.job_submission.pb.job_service_pb2 import JobResponse
from sc_sdk.utils.time_utils import now

DUMMY_ORGANIZATION_ID = "000000000000000000000001"
DUMMY_WORKSPACE_ID = "652651cd3ffd5b3dc7f1d391"

DUMMY_JOB_KEY = json.dumps({"job_key": "job_value"})
DUMMY_PAYLOAD = {
    "task_id": "637e2633e9d5bada747c6311",
    "dataset_storage_id": "637e2633e9d5bada747c6309",
}
DUMMY_METADATA = {
    "project_name": "test_project",
    "model_architecture": "EfficientNet-B0",
    "model_version": 1,
}
DUMMY_AUTHOR = ID("author_uid")
DUMMY_TIME = now()

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def fxt_session_ctx():
    logger.info("Initializing session (fixture 'fxt_session_ctx')")
    session = make_session(
        organization_id=DUMMY_ORGANIZATION_ID,
        workspace_id=DUMMY_WORKSPACE_ID,
        source=RequestSource.INTERNAL,
    )
    with session_context(session=session):
        yield session


@pytest.fixture
def fxt_step_details():
    yield JobStepDetails(
        index=1,
        task_id="task_id",
        step_name="step_name",
        state=JobTaskState.WAITING,
        progress=0.5,
        message=None,
        warning="warning",
    )


@pytest.fixture
def fxt_dummy_job_id():
    return str(ObjectId())


@pytest.fixture
def fxt_job(fxt_step_details, fxt_dummy_job_id):
    yield Job(
        id=fxt_dummy_job_id,
        workspace_id=ID(DUMMY_WORKSPACE_ID),
        type="train",
        priority=0,
        job_name="Train",
        key=DUMMY_JOB_KEY,
        state=JobState.SUBMITTED,
        state_group=JobStateGroup.SCHEDULED,
        step_details=(fxt_step_details,),
        payload=DUMMY_PAYLOAD,
        metadata=DUMMY_METADATA,
        creation_time=DUMMY_TIME,
        author=DUMMY_AUTHOR,
        cancellation_info=JobCancellationInfo(cancellable=True, is_cancelled=False, cancel_time=None, user_uid=None),
        project_id=ID("project_id"),
        start_time=DUMMY_TIME,
        end_time=DUMMY_TIME,
        executions=JobFlyteExecutions(main=JobMainFlyteExecution()),
        session=make_session(
            organization_id=ID(DUMMY_ORGANIZATION_ID),
            workspace_id=ID(DUMMY_WORKSPACE_ID),
        ),
        telemetry=Telemetry(),
        cost=JobCost(
            requests=(JobResource(amount=100, unit="images"),),
            lease_id="lease_id",
            consumed=(JobConsumedResource(amount=100, unit="images", consuming_date=DUMMY_TIME, service="training"),),
            reported=False,
        ),
    )


@pytest.fixture
def fxt_workspace_job(fxt_step_details, fxt_dummy_job_id):
    yield Job(
        id=fxt_dummy_job_id,
        workspace_id=ID(DUMMY_WORKSPACE_ID),
        type="train",
        priority=0,
        job_name="Train",
        key=DUMMY_JOB_KEY,
        state=JobState.SUBMITTED,
        state_group=JobStateGroup.SCHEDULED,
        step_details=(fxt_step_details,),
        payload=DUMMY_PAYLOAD,
        metadata=DUMMY_METADATA,
        creation_time=DUMMY_TIME,
        author=DUMMY_AUTHOR,
        cancellation_info=JobCancellationInfo(cancellable=True, is_cancelled=False, cancel_time=None, user_uid=None),
        start_time=DUMMY_TIME,
        end_time=DUMMY_TIME,
        executions=JobFlyteExecutions(main=JobMainFlyteExecution()),
        session=make_session(
            organization_id=ID(DUMMY_ORGANIZATION_ID),
            workspace_id=ID(DUMMY_WORKSPACE_ID),
        ),
        telemetry=Telemetry(),
    )


@pytest.fixture
def fxt_job_rest(fxt_dummy_job_id):
    return {
        "id": fxt_dummy_job_id,
        "type": "train",
        "creation_time": DUMMY_TIME.isoformat(),
        "start_time": DUMMY_TIME.isoformat(),
        "end_time": DUMMY_TIME.isoformat(),
        "name": "Train",
        "author": DUMMY_AUTHOR,
        "state": JobStateGroup.SCHEDULED.name.lower(),
        "steps": [
            {
                "message": None,
                "index": 1,
                "progress": 0.5,
                "state": "waiting",
                "step_name": "step_name",
                "warning": "warning",
            },
        ],
        "cancellation_info": {
            "cancellable": True,
            "is_cancelled": False,
            "user_uid": None,
            "cancel_time": None,
        },
        "metadata": DUMMY_METADATA,
        "cost": {
            "requests": [{"amount": 100, "unit": "images"}],
            "consumed": [{"amount": 100, "unit": "images"}],
        },
    }


@pytest.fixture
def fxt_job_response(fxt_job, fxt_step_details, fxt_dummy_job_id):
    yield JobResponse(
        id=fxt_dummy_job_id,
        workspace_id=str(ID(DUMMY_WORKSPACE_ID)),
        type="train",
        priority=0,
        job_name="Train",
        key=DUMMY_JOB_KEY,
        state=JobState.SUBMITTED.name,
        state_group=JobStateGroup.SCHEDULED.name,
        step_details=[
            JobResponse.StepDetails(
                index=fxt_step_details.index,
                task_id=str(fxt_step_details.task_id),
                step_name=fxt_step_details.step_name,
                state=fxt_step_details.state.name,
                progress=fxt_step_details.progress,
                message=fxt_step_details.message,
                warning=fxt_step_details.warning,
            )
        ],
        payload=json.dumps(DUMMY_PAYLOAD),
        metadata=json.dumps(DUMMY_METADATA),
        creation_time=DUMMY_TIME.isoformat(),
        author=DUMMY_AUTHOR,
        project_id=str(fxt_job.project_id),
        cancellation_info=JobResponse.CancellationInfo(
            is_cancelled=fxt_job.cancellation_info.is_cancelled,
            user_uid=fxt_job.cancellation_info.user_uid,
            cancel_time=fxt_job.cancellation_info.cancel_time,  # type: ignore
            request_time=fxt_job.cancellation_info.request_time,  # type: ignore
        ),
        start_time=fxt_job.start_time.isoformat(),
        end_time=fxt_job.end_time.isoformat(),
        cost=JobResponse.JobCost(
            requests=[JobResponse.JobResource(amount=100, unit="images")],
            consumed=[JobResponse.JobResource(amount=100, unit="images")],
        ),
    )
