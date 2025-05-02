#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""
Job mapper module
"""

from typing import Any

from model.job import (
    Job,
    JobCancellationInfo,
    JobConsumedResource,
    JobCost,
    JobFlyteExecutions,
    JobGpuRequest,
    JobMainFlyteExecution,
    JobResource,
    JobRevertFlyteExecution,
    JobStepDetails,
    JobTaskExecutionBranch,
)
from model.job_state import JobGpuRequestState, JobState, JobStateGroup, JobTaskState
from model.telemetry import Telemetry

from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo
from iai_core_py.repos.mappers.mongodb_mappers.session_mapper import SessionToMongo


def _opt(document: dict, key: str) -> Any | None:
    """
    Maps an optional document field
    :param document: MongoDB document
    :param key: field name
    :return value if key is found, None otherwise
    """
    return document.get(key)


def _opt_datetime(document: dict, key: str) -> Any | None:
    """
    Maps an optional document datetime field
    :param document: MongoDB document
    :param key: field name
    :return datetime value if key is found, None otherwise
    """
    return DatetimeToMongo().backward(document[key]) if key in document else None


class JobTaskExecutionBranchMapper(IMapperSimple[JobTaskExecutionBranch, dict]):
    """
    Job task execution branch (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def backward(instance: dict) -> JobTaskExecutionBranch:
        """
        Maps a MongoDB dict to JobTaskExecutionBranch entity
        :param instance: MongoDB dict
        :return JobTaskExecutionBranch entity
        """
        return JobTaskExecutionBranch(
            condition=instance["condition"],
            branch=instance["branch"],
        )

    @staticmethod
    def forward(branch: JobTaskExecutionBranch) -> dict:
        """
        Maps a JobTaskExecutionBranch entity to MongoDB dict
        :param branch: JobTaskExecutionBranch entity
        :return: MongoDB dict
        """
        return {
            "condition": branch.condition,
            "branch": branch.branch,
        }


class JobStepDetailsMapper(IMapperSimple[JobStepDetails, dict]):
    """
    Job step details mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def backward(instance: dict) -> JobStepDetails:
        """
        Maps a MongoDB dict to JobTaskProgress entity
        :param instance: MongoDB dict
        :return JobTaskProgress entity
        """
        return JobStepDetails(
            index=instance["index"],
            task_id=instance["task_id"],
            step_name=instance["step_name"],
            state=JobTaskState[instance["state"]],
            progress=instance.get("progress", -1),
            message=_opt(instance, "message"),
            warning=instance.get("warning"),
            branches=(
                tuple(JobTaskExecutionBranchMapper.backward(branch) for branch in instance["branches"])
                if "branches" in instance
                else None
            ),
            start_time=_opt_datetime(instance, "start_time"),
            end_time=_opt_datetime(instance, "end_time"),
        )

    @staticmethod
    def forward(step_details: JobStepDetails) -> dict:
        """
        Maps a JobStepDetails entity to MongoDB dict
        :param step_details: JobStepDetails entity
        :return dict MongoDB dict
        """
        result = {
            "index": step_details.index,
            "task_id": step_details.task_id,
            "step_name": step_details.step_name,
            "state": step_details.state.value,
        }
        if step_details.progress is not None:
            result["progress"] = step_details.progress
        if step_details.message is not None:
            result["message"] = step_details.message
        if step_details.branches is not None:
            result["branches"] = [JobTaskExecutionBranchMapper.forward(branch) for branch in step_details.branches]
        if step_details.start_time is not None:
            result["start_time"] = step_details.start_time
        if step_details.end_time is not None:
            result["end_time"] = step_details.end_time
        if step_details.warning is not None:
            result["warning"] = step_details.warning
        return result


class JobCancellationInfoMapper(IMapperSimple[JobCancellationInfo, dict]):
    """
    Job cancellation info mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: JobCancellationInfo) -> dict:
        """
        Maps a JobCancellationInfo entity to MongoDB dict

        :param instance: JobCancellationInfo entity
        :return: MongoDB dict
        """
        doc: dict = {
            "cancellable": instance.cancellable,
            "is_cancelled": instance.is_cancelled,
            "delete_job": instance.delete_job,
        }
        if instance.user_uid is not None:
            doc["user_uid"] = instance.user_uid
        if instance.cancel_time is not None:
            doc["cancel_time"] = instance.cancel_time
        if instance.request_time is not None:
            doc["request_time"] = instance.request_time
        return doc

    @staticmethod
    def backward(instance: dict) -> JobCancellationInfo:
        """
        Maps a MongoDB dict to JobCancellationInfo entity
        :param instance: MongoDB dict
        :return JobTaskProgress entity
        """
        return JobCancellationInfo(
            cancellable=bool(instance.get("cancellable", True)),
            is_cancelled=bool(instance["is_cancelled"]),
            user_uid=_opt(instance, "user_uid"),
            cancel_time=_opt_datetime(instance, "cancel_time"),
            request_time=_opt_datetime(instance, "request_time"),
            delete_job=bool(instance.get("delete_job", False)),
        )


class JobMainFlyteExecutionMapper(IMapperSimple[JobMainFlyteExecution, dict]):
    """
    Job main Flyte execution mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: JobMainFlyteExecution) -> dict:
        """
        Maps a JobMainFlyteExecution entity to MongoDB dict

        :param instance: JobMainFlyteExecution entity
        :return: MongoDB dict
        """
        doc: dict = {}
        if instance.launch_plan_id is not None:
            doc["launch_plan_id"] = instance.launch_plan_id
        if instance.execution_id is not None:
            doc["execution_id"] = instance.execution_id
        if instance.start_retry_counter is not None:
            doc["start_retry_counter"] = instance.start_retry_counter
        if instance.cancel_retry_counter is not None:
            doc["cancel_retry_counter"] = instance.cancel_retry_counter
        if instance.process_start_time is not None:
            doc["process_start_time"] = instance.process_start_time
        return doc

    @staticmethod
    def backward(instance: dict) -> JobMainFlyteExecution:
        """
        Maps a MongoDB dict to JobMainFlyteExecution entity
        :param instance: MongoDB dict
        :return JobMainFlyteExecution entity
        """
        return JobMainFlyteExecution(
            launch_plan_id=_opt(instance, "launch_plan_id"),
            execution_id=_opt(instance, "execution_id"),
            start_retry_counter=_opt(instance, "start_retry_counter"),
            cancel_retry_counter=_opt(instance, "cancel_retry_counter"),
            process_start_time=_opt_datetime(instance, "process_start_time"),
        )


class JobRevertFlyteExecutionMapper(IMapperSimple[JobRevertFlyteExecution, dict]):
    """
    Job revert Flyte execution mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: JobRevertFlyteExecution) -> dict:
        """
        Maps a JobRevertFlyteExecution entity to MongoDB dict

        :param instance: JobRevertFlyteExecution entity
        :return: MongoDB dict
        """
        doc: dict = {}
        if instance.execution_id is not None:
            doc["execution_id"] = instance.execution_id
        if instance.start_retry_counter is not None:
            doc["start_retry_counter"] = instance.start_retry_counter
        if instance.process_start_time is not None:
            doc["process_start_time"] = instance.process_start_time
        return doc

    @staticmethod
    def backward(instance: dict) -> JobRevertFlyteExecution:
        """
        Maps a MongoDB dict to JobRevertFlyteExecution entity
        :param instance: MongoDB dict
        :return JobRevertFlyteExecution entity
        """
        return JobRevertFlyteExecution(
            execution_id=_opt(instance, "execution_id"),
            start_retry_counter=_opt(instance, "start_retry_counter"),
            process_start_time=_opt_datetime(instance, "process_start_time"),
        )


class JobExecutionsMapper(IMapperSimple[JobFlyteExecutions, dict]):
    """
    Job Flyte executions mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: JobFlyteExecutions) -> dict:
        """
        Maps a JobFlyteExecutions entity to MongoDB dict

        :param instance: JobFlyteExecutions entity
        :return: MongoDB dict
        """
        doc = {"main": JobMainFlyteExecutionMapper.forward(instance.main)}
        if instance.revert is not None:
            doc["revert"] = JobRevertFlyteExecutionMapper.forward(instance.revert)
        return doc

    @staticmethod
    def backward(instance: dict) -> JobFlyteExecutions:
        """
        Maps a MongoDB dict to JobFlyteExecutions entity
        :param instance: MongoDB dict
        :return JobFlyteExecutions entity
        """
        return JobFlyteExecutions(
            main=JobMainFlyteExecutionMapper.backward(instance["main"]),
            revert=JobRevertFlyteExecutionMapper.backward(instance["revert"]) if "revert" in instance else None,
        )


class TelemetryMapper(IMapperSimple[Telemetry, dict]):
    """
    Telemetry mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: Telemetry) -> dict:
        """
        Maps a Telemetry entity to a MongoDB dict

        :param instance: Telemetry entity
        :return: MongoDB dict
        """
        return {"context": instance.context}

    @staticmethod
    def backward(instance: dict) -> Telemetry:
        """
        Maps a MongoDB dict to Telemetry entity

        :param instance: MongoDB dict
        :return User entity
        """
        return Telemetry(context=instance.get("context", ""))


class JobGpuRequestMapper(IMapperSimple[JobGpuRequest, dict]):
    """
    JobGpuRequest mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: JobGpuRequest) -> dict:
        """
        Maps a JobGpuRequest entity to a MongoDB dict

        :param instance: JobGpuRequest entity
        :return: MongoDB dict
        """
        return {"num_required": instance.num_required, "state": instance.state.value}

    @staticmethod
    def backward(instance: dict) -> JobGpuRequest:
        """
        Maps a MongoDB dict to JobGpuRequest entity

        :param instance: MongoDB dict
        :return JobGpuRequest entity
        """
        return JobGpuRequest(num_required=instance["num_required"], state=JobGpuRequestState(instance["state"]))


class JobResourceMapper(IMapperSimple[JobResource, dict]):
    """
    JobResource mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: JobResource) -> dict:
        """
        Maps a JobResource entity to a MongoDB dict

        :param instance: JobResource entity
        :return: MongoDB dict
        """
        return {"amount": instance.amount, "unit": instance.unit}

    @staticmethod
    def backward(instance: dict) -> JobResource:
        """
        Maps a MongoDB dict to JobResource entity

        :param instance: MongoDB dict
        :return: JobResource entity
        """
        return JobResource(amount=instance["amount"], unit=instance["unit"])


class JobConsumedResourceMapper(IMapperSimple[JobConsumedResource, dict]):
    """
    JobConsumedResource mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: JobConsumedResource) -> dict:
        """
        Maps a JobConsumedResource entity to a MongoDB dict

        :param instance: JobConsumedResource entity
        :return: MongoDB dict
        """
        return {
            "amount": instance.amount,
            "unit": instance.unit,
            "consuming_date": DatetimeToMongo.forward(instance.consuming_date),
            "service": instance.service,
        }

    @staticmethod
    def backward(instance: dict) -> JobConsumedResource:
        """
        Maps a MongoDB dict to JobConsumedResource entity

        :param instance: MongoDB dict
        :return: JobConsumedResource entity
        """
        return JobConsumedResource(
            amount=instance["amount"],
            unit=instance["unit"],
            consuming_date=DatetimeToMongo.backward(instance["consuming_date"]),
            service=instance.get("service", "unknown"),  # backward compatibility: some docs may not have this field
        )


class JobCostMapper(IMapperSimple[JobCost, dict]):
    """
    JobCost mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: JobCost) -> dict:
        """
        Maps a JobCost entity to a MongoDB dict

        :param instance: JobCost entity
        :return: MongoDB dict
        """
        return {
            "requests": [JobResourceMapper.forward(request) for request in instance.requests],
            "lease_id": instance.lease_id,
            "consumed": [JobConsumedResourceMapper.forward(consumed) for consumed in instance.consumed],
            "reported": instance.reported,
        }

    @staticmethod
    def backward(instance: dict) -> JobCost:
        """
        Maps a MongoDB dict to JobCost entity

        :param instance: MongoDB dict
        :return: JobCost entity
        """
        return JobCost(
            requests=tuple(JobResourceMapper.backward(request) for request in instance["requests"]),
            lease_id=instance["lease_id"],
            consumed=tuple(JobConsumedResourceMapper.backward(consumed) for consumed in instance["consumed"]),
            reported=instance["reported"],
        )


class JobMapper(IMapperSimple[Job, dict]):
    """
    Job mapper (from MongoDB dict) to a "business layer" level object
    """

    @staticmethod
    def forward(instance: Job) -> dict:
        """
        Maps a Job instance to a MondogDB instance

        :param instance: Job instance
        :return: MongoDB dict
        """
        doc = {
            "_id": IDToMongo.forward(instance.id_),
            "workspace_id": IDToMongo.forward(instance.workspace_id),
            "type": instance.type,
            "priority": instance.priority,
            "job_name": instance.job_name,
            "key": instance.key,
            "state": instance.state.value,
            "state_group": instance.state_group.value,
            "step_details": [JobStepDetailsMapper.forward(step) for step in instance.step_details],
            "payload": instance.payload,
            "metadata": instance.metadata,
            "creation_time": instance.creation_time,
            "author": IDToMongo.forward(instance.author),
            "cancellation_info": JobCancellationInfoMapper.forward(instance.cancellation_info),
            "executions": JobExecutionsMapper.forward(instance.executions),
            "session": SessionToMongo.forward(instance.session),
        }
        if instance.gpu is not None:
            doc["gpu"] = JobGpuRequestMapper.forward(instance.gpu)
        if instance.project_id is not None:
            doc["project_id"] = IDToMongo.forward(instance.project_id)
        if instance.start_time is not None:
            doc["start_time"] = instance.start_time
        if instance.end_time is not None:
            doc["end_time"] = instance.end_time
        if instance.telemetry is not None:
            doc["telemetry"] = TelemetryMapper.forward(instance.telemetry)
        if instance.cost is not None:
            doc["cost"] = JobCostMapper.forward(instance.cost)
        return doc

    @staticmethod
    def backward(instance: dict) -> Job:
        """
        Maps a MongoDB instance to Job entity
        :param instance: MongoDB document
        :return Job entity
        """
        return Job(
            id=IDToMongo().backward(instance["_id"]),
            workspace_id=IDToMongo().backward(instance["workspace_id"]),
            type=instance["type"],
            priority=instance["priority"],
            job_name=instance["job_name"],
            key=instance["key"],
            state=JobState(instance["state"]),
            state_group=JobStateGroup[instance["state_group"]],
            step_details=tuple(
                JobStepDetailsMapper.backward(task_progress) for task_progress in instance["step_details"]
            ),
            payload=instance["payload"],
            metadata=instance["metadata"],
            creation_time=DatetimeToMongo().backward(instance["creation_time"]),
            author=IDToMongo.backward(instance["author"]),
            project_id=IDToMongo().backward(instance["project_id"]) if "project_id" in instance else None,
            start_time=_opt_datetime(instance, "start_time"),
            end_time=_opt_datetime(instance, "end_time"),
            executions=JobExecutionsMapper.backward(instance["executions"]),
            session=SessionToMongo.backward(instance["session"]),
            gpu=JobGpuRequestMapper.backward(instance["gpu"]) if "gpu" in instance else None,
            cancellation_info=JobCancellationInfoMapper.backward(instance["cancellation_info"]),
            telemetry=TelemetryMapper.backward(instance.get("telemetry", {})),
            cost=JobCostMapper.backward(instance["cost"]) if "cost" in instance else None,
        )
