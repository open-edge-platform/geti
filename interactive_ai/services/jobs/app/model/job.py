#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""
Job model module
"""

from dataclasses import dataclass
from datetime import datetime

from model.job_state import JobGpuRequestState, JobState, JobStateGroup, JobTaskState
from model.telemetry import Telemetry

from geti_types import ID, PersistentEntity, Session, make_session
from iai_core.utils.time_utils import now


@dataclass
class JobTaskExecutionBranch:
    """
    Job execution condition
    Identifies that the task is executed in a conditional branch. Execution condition has a name and
    two (then-else) branches. Information about condition name and branch name is stored in this object.

    parent_node                 Execution condition node
                                In an execution dag conditional is represented as a parent node with its ID, i.e. n0
                                and a name.
    branch                      Execution branch name
                                In an execution dag conditional has two downstream branches, usually n0-n0 (then case)
                                and n0-n1 (else case). These nodes also have names, i.e. do_nothing

    """

    condition: str
    branch: str


@dataclass
class JobStepDetails:
    """
    Job step details model, a step (AKA task) represents a unit of execution

    index                       Number of the step/task
    task_id                     Task identifier
    step_name                   Human-readable name for the step
    state                       Task state. For available values, see
                                :class:`~model.job_state.JobTaskState`.
    progress                    Step progress, from 0 to 100
    message                     Step status message
    warning                     Step warning message
    branches                    Job execution branches this task belongs to. One task might belong to
                                multiple nested conditionals.
    start_time                  Timestamp of a moment when step execution starts
    end_time                    Timestamp of a moment when step execution stops
    """

    index: int
    task_id: str
    step_name: str
    state: JobTaskState
    progress: float = -1
    message: str | None = None
    warning: str | None = None
    branches: tuple[JobTaskExecutionBranch, ...] | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    def get_branch_value(self, condition: str) -> str | None:
        """
        Returns a job step branch value by a branch condition name
        :param condition: condition name
        :return str: branch value or None if step is not a part of specified condition
        """
        return (
            next(
                (branch.branch for branch in self.branches if branch.condition == condition),
                None,
            )
            if self.branches is not None
            else None
        )


@dataclass
class JobCancellationInfo:
    """
    Job cancellation info

    cancellable            Boolean indicating if the job can be cancelled by the user after running
    is_cancelled           Boolean indicating if the job is cancelled by the user
    user_uid               UID of the user that requested cancellation
    cancel_time            Time when job was cancelled.
    request_time           Time when the cancellation of the job was requested.
    delete_job             If the job should be deleted after cancellation.
    """

    cancellable: bool = True
    is_cancelled: bool = False
    user_uid: str | None = None
    cancel_time: datetime | None = None
    request_time: datetime | None = None
    delete_job: bool = False


@dataclass
class JobMainFlyteExecution:
    """
    Job main Flyte execution

    launch_plan_id              Flyte launch plan ID
    execution_id                Flyte execution ID
    start_retry_counter         Counter defining number of execution start retries
    cancel_retry_counter        Counter defining number of execution cancel retries
    process_start_time          Timestamp of a moment when execution has been picked for start or canceling by scheduler
    """

    launch_plan_id: str | None = None
    execution_id: str | None = None
    start_retry_counter: int | None = None
    cancel_retry_counter: int | None = None
    process_start_time: datetime | None = None


@dataclass
class JobRevertFlyteExecution:
    """
    Job revert Flyte execution

    launch_plan_id              Flyte launch plan ID
    execution_id                Flyte execution ID
    """

    execution_id: str | None = None
    start_retry_counter: int | None = None
    process_start_time: datetime | None = None


@dataclass
class JobFlyteExecutions:
    """
    Job Flyte executions

    main                        Main Flyte execution
    revert                      Revert Flyte execution (in case of failure or cancellation)
    """

    main: JobMainFlyteExecution
    revert: JobRevertFlyteExecution | None = None


@dataclass
class JobGpuRequest:
    """
    Job GPU requirements

    num_required                Number of GPUs required for job execution
    state                       GPU request state
    """

    num_required: int
    state: JobGpuRequestState = JobGpuRequestState.WAITING


@dataclass
class JobResource:
    """
    Job priced resource information

    amount                      Resource amount, i.e. 100
    unit                        Resource unit, i.e. images
    """

    amount: int
    unit: str


@dataclass
class JobConsumedResource(JobResource):
    """
    Job consumed resource information

    consuming_date              Resources consuming timestamp
    service                     Service, which has consumed the resources
    """

    consuming_date: datetime
    service: str


@dataclass
class JobCost:
    """
    Job cost information

    requests                    List of priced resources which job plans to utilize
    lease_id                    Credits lease identifier
    consumed                    List of already consumed priced resources
    reported                    Flag indicating that consumed resources have been reported already after job finish
                                or cancellation
    """

    requests: tuple[JobResource, ...]
    lease_id: str
    consumed: tuple[JobConsumedResource, ...]
    reported: bool


class Job(PersistentEntity):
    """
    Job model

    id_                         Job identifier
    workspace_id                ID of a workspace job belongs to
    type                        Job type (train, test, etc.). Defines which workflow to execute in Flyte
    priority                    Job priority
    job_name                    Job human-readable name
    key                         Job key, two jobs having the same key are considered as duplicates
                                There cannot be more than 1 running job with certain key.
                                There cannot be more than 1 SUBMITTED non-cancelled job with certain key.
    state                       Job state. For available values, see
                                :class:`~model.job_state.JobState`.
    state_group                 Job state group (UI state). For available values, see
                                :class:`~model.job_state.JobStateGroup`.
    step_details                Job steps details (multiple). For more information, see
                                :class:`~model.job.JobStepDetails`.
    payload                     Job payload (all the data required for job's execution)
    metadata                    Job metadata (human friendly job parameters)
    creation_time               Job creation timestamp
    author                      Job author (user id)
    cancellation_info           Contains details regarding the cancellation of the Job
    telemetry                   Contains telemetry data related to the Job
    project_id                  ID of a project job belongs to, only for project related jobs
    start_time                  Job start timestamp
    end_time                    Job finish\failure timestamp
    executions                  Job Flyte executions
    cost                        Job cost information in case if credits should be charged for job execution
    """

    def __init__(  # noqa: PLR0913
        self,
        id: ID,
        workspace_id: ID,
        type: str,
        priority: int,
        job_name: str,
        key: str,
        state: JobState,
        state_group: JobStateGroup,
        step_details: tuple[JobStepDetails, ...],
        payload: dict,
        metadata: dict,
        creation_time: datetime,
        author: ID,
        cancellation_info: JobCancellationInfo,
        executions: JobFlyteExecutions,
        session: Session,
        gpu: JobGpuRequest | None = None,
        telemetry: Telemetry | None = None,
        project_id: ID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        ephemeral: bool = True,
        cost: JobCost | None = None,
    ) -> None:
        super().__init__(id_=id, ephemeral=ephemeral)
        self.workspace_id = workspace_id
        self.type = type
        self.priority = priority
        self.job_name = job_name
        self.key = key
        self.state = state
        self.state_group = state_group
        self.step_details = step_details
        self.payload = payload
        self.metadata = metadata
        self.creation_time = creation_time
        self.author = author
        self.cancellation_info = cancellation_info
        self.executions = executions
        self.session = session
        self.gpu = gpu
        self.telemetry = telemetry if telemetry is not None else Telemetry()
        self.project_id = project_id
        self.start_time = start_time
        self.end_time = end_time
        self.cost = cost

    @property
    def id(self) -> ID:
        return self.id_

    def __repr__(self) -> str:
        """
        Returns the string representation of the Job instance (only basic info is included)
        """
        return (
            f"{self.__class__.__name__}(id={self.id_}"
            f", type='{self.type}'"
            f", job_name='{self.job_name}'"
            f", key='{self.key}'"
            f", state={self.state}"
            f", session={self.session}"
        )


class NullJob(Job):
    def __init__(self) -> None:
        super().__init__(
            id=ID(),
            workspace_id=ID(),
            type="",
            priority=-1,
            job_name="",
            key="",
            state=JobState.FAILED,
            state_group=JobStateGroup.FAILED,
            step_details=(),
            payload={},
            metadata={},
            creation_time=now(),
            author=ID(),
            cancellation_info=JobCancellationInfo(),
            executions=JobFlyteExecutions(main=JobMainFlyteExecution()),
            session=make_session(),
        )

    def __repr__(self) -> str:
        return "NullJob()"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NullJob)
