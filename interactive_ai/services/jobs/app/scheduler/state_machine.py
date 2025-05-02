# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Job scheduler state machine module
"""

import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pymongo import ReturnDocument

from model.job import Job, JobConsumedResource, JobStepDetails
from model.job_state import JobGpuRequestState, JobState, JobStateGroup, JobTaskState
from model.mapper.job_mapper import JobConsumedResourceMapper, JobMapper, JobStepDetailsMapper
from scheduler.job_repo import SessionBasedSchedulerJobRepo

from geti_kafka_tools import publish_event
from geti_spicedb_tools import SpiceDB
from geti_types import CTX_SESSION_VAR, ID, Singleton
from iai_core_py.repos.base.constants import ORGANIZATION_ID_FIELD_NAME, WORKSPACE_ID_FIELD_NAME
from iai_core_py.repos.mappers import IDToMongo
from iai_core_py.utils.time_utils import now

logger = logging.getLogger(__name__)


class StateMachine(metaclass=Singleton):
    """
    Job state machine

    Main entry point for jobs state machine. All the jobs transitions between different states
    are done using this module. This module is available only to Jobs scheduler and not exposed to the outside.

    This module contains all the business logic, however since we have manipulations with MongoDB documents as a part
    of business logic, it also has MongoDB dependencies.

    """

    #################################################################################
    # Organizations                                                                 #
    #################################################################################

    def get_session_ids_with_jobs_not_in_final_state(self) -> dict[ID, ID]:
        """
        Returns ID's of organizations with workspaces which have jobs in non-final states

        This method operates jobs for all the organizations!

        :return dict[ID, ID]: ID's of organizations mapping to a workspace
        """
        logger.debug("Getting organizations with jobs not in final state")
        ids = {}
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            aggr_pipeline = [
                {
                    "$match": {
                        "state": {"$lt": JobState.FINISHED.value},
                    }
                },
            ]
            documents = job_repo._collection.aggregate(aggr_pipeline, allowDiskUse=True)
            for doc in documents:
                organization_id = IDToMongo.backward(doc[ORGANIZATION_ID_FIELD_NAME])
                workspace_id = IDToMongo.backward(doc[WORKSPACE_ID_FIELD_NAME])
                ids[organization_id] = workspace_id
            return ids

    #################################################################################
    # CRUD Operations                                                               #
    #################################################################################

    def get_by_id(self, job_id: ID) -> Job | None:
        """
        Returns a job by its ID
        :param job_id: identifier of a job to be returned
        :return found job or None
        """
        logger.debug(f"Getting job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            document = job_repo.get_document_by_id(job_id)
            return JobMapper.backward(document) if document is not None else None

    def find_jobs_ids_by_project_id(self, project_id: ID) -> tuple[ID, ...]:
        """
        Returns ID's of jobs belonging to the project
        :param project_id: project ID
        :return a tuple with jobs ID's
        """
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            documents = job_repo.aggregate_read(
                [
                    {
                        "$match": {
                            "project_id": str(project_id),
                        }
                    }
                ]
            )
            return tuple(IDToMongo.backward(document["_id"]) for document in documents)

    def delete_job(self, job_id: ID) -> bool:
        """
        Deletes a job by its ID.
        Removes document from repo & relation from SpiceDB.

        :param job_id: identifier of a job to be deleted
        """
        logger.debug(f"Deleting job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session() as session, session.start_transaction():
            deleted = job_repo.delete_by_id(job_id)
            if deleted:
                SpiceDB().delete_job(job_id=str(job_id))
                logger.info(f"Job {job_id} successfully deleted")
            else:
                logger.info(f"Job {job_id} seems already to be deleted")
            return deleted

    #################################################################################
    # Cancellation                                                                  #
    #################################################################################

    def mark_cancelled_and_deleted(self, job_id: ID) -> bool:
        """
        Marks job as cancelled with delete_job flag set to True
        :param job_id: identifier of a job to mark
        :return: True if the job is marked as cancelled, False otherwise
        """
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            return job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "cancellation_info.is_cancelled": True,
                        "cancellation_info.request_time": now(),
                        "cancellation_info.delete_job": True,
                    }
                },
            )

    #################################################################################
    # Scheduling / Running                                                          #
    #################################################################################

    def find_and_lock_job_for_scheduling(self) -> Job | None:
        """
        Finds one job for scheduling and updates its state to SCHEDULING together with filling process_start_time

        This method operates jobs for all the organizations!

        :return job if it's found, None otherwise
        """
        logger.debug("Finding and locking a job for scheduling")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            document = job_repo._collection.find_one_and_update(
                filter={
                    "state": JobState.READY_FOR_SCHEDULING.value,
                    "cancellation_info.is_cancelled": False,
                },
                update={
                    "$set": {
                        "state": JobState.SCHEDULING.value,
                        "state_group": JobStateGroup.SCHEDULED.value,
                        "executions.main.process_start_time": now(),
                    }
                },
                upsert=False,
                return_document=ReturnDocument.AFTER,
            )
            return None if document is None else JobMapper.backward(document)

    def reset_scheduling_jobs(self, threshold: datetime) -> int:
        """
        Resets all SCHEDULING jobs which are older than specified threshold back to SUBMITTED state
        and increments start_retry_counter

        This method operates jobs for all the organizations!

        :param threshold: process_start_time reset threshold
        :return int: number of jobs modified
        """
        logger.debug(f"Resetting scheduling jobs which are older than {threshold}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            count = job_repo._collection.update_many(
                filter={
                    "state": JobState.SCHEDULING.value,
                    "executions.main.process_start_time": {"$lt": threshold},
                },
                update={
                    "$set": {
                        "state": JobState.SUBMITTED.value,
                        "state_group": JobStateGroup.SCHEDULED.value,
                    },
                    "$unset": {
                        "executions.main.process_start_time": "",
                    },
                    "$inc": {
                        "executions.main.start_retry_counter": 1,
                    },
                },
            ).modified_count
            if count > 0:
                logger.warning(f"Number of scheduling jobs which were reset={count}")
            return count

    def reset_scheduling_job(self, job_id: ID) -> bool:
        """
        Resets SCHEDULING job by its ID and increments start_retry_counter
        :param job_id: identifier of a job to reset state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Resetting a scheduling job {job_id} to submitted state")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": JobState.SUBMITTED.value,
                        "state_group": JobStateGroup.SCHEDULED.value,
                    },
                    "$unset": {
                        "executions.main.process_start_time": "",
                    },
                    "$inc": {
                        "executions.main.start_retry_counter": 1,
                    },
                },
            )
            if updated:
                logger.info(f"A scheduling job {job_id} has been reset to submitted state")
            return updated

    def set_scheduled_state(
        self,
        job_id: ID,
        flyte_launch_plan_id: str,
        flyte_execution_id: str,
        step_details: Sequence[JobStepDetails],
    ) -> bool:
        """
        Updates job's state to SCHEDULED and sets Flyte related fields
        :param job_id: identifier of a job to update state
        :param flyte_launch_plan_id: Flyte launch plan ID
        :param flyte_execution_id: Flyte execution ID
        :param step_details: Flyte user visible tasks
        :return bool: True if job document has been updated
        """
        logger.debug(
            f"Setting a scheduled state for job {job_id}, flyte_launch_plan_id={flyte_launch_plan_id}, "
            + f"flyte_execution_id={flyte_execution_id}, step_details={step_details}"
        )
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": JobState.SCHEDULED.value,
                        "state_group": JobStateGroup.SCHEDULED.value,
                        "executions.main.launch_plan_id": flyte_launch_plan_id,
                        "executions.main.execution_id": flyte_execution_id,
                        "step_details": [JobStepDetailsMapper.forward(step_details) for step_details in step_details],
                    },
                    "$unset": {"executions.main.process_start_time": ""},
                },
            )
            if updated:
                logger.info(f"Job {job_id} has been set to scheduled state")
            return updated

    def set_running_state(self, job_id: ID) -> bool:
        """
        Updates job's state to RUNNING and sets start time
        :param job_id: identifier of a job to update state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting a running state for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": JobState.RUNNING.value,
                        "state_group": JobStateGroup.RUNNING.value,
                        "start_time": now(),
                    }
                },
            )
            if updated:
                logger.info(f"Job {job_id} has been set to running state")
            return updated

    #################################################################################
    # Tasks & progress                                                              #
    #################################################################################

    def set_step_details(  # noqa: PLR0913
        self,
        job_id: ID,
        task_id: str,
        state: JobTaskState | None,
        progress: float | None = None,
        message: str | None = None,
        warning: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> bool:
        """
        Updates job's step details

        :param job_id: identifier of a job to update step details for
        :param task_id: identifier of a job task
        :param state: task state, not updated if None
        :param progress: task progress, not updated if None
        :param message: task message, not updated if None
        :param warning: task warning, not updated if None
        :param start_time: start time of the step, not updated if None
        :param end_time: end time of the step, not updated if None
        :return bool: True if job document has been updated
        """
        logger.debug(
            f"Setting step details for job {job_id}, task_id={task_id}, "
            + f"state={state}, progress={progress}, message={message}"
        )
        update_set: dict[str, Any] = {}
        if state is not None:
            update_set["step_details.$[task].state"] = state.value
        if progress is not None:
            update_set["step_details.$[task].progress"] = progress
        if message is not None:
            update_set["step_details.$[task].message"] = message
        if warning is not None:
            update_set["step_details.$[task].warning"] = warning
        if start_time is not None:
            update_set["step_details.$[task].start_time"] = start_time
        if end_time is not None:
            update_set["step_details.$[task].end_time"] = end_time
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={"$set": update_set},
                array_filters=[
                    {"task.task_id": task_id},
                ],
            )
            if updated:
                logger.info(f"Job's {job_id} step {task_id} has been updated")
            return updated

    def update_metadata(self, job_id: ID, metadata: dict) -> bool:
        """
        Updates job's metadata

        :param job_id: identifier of a job to update metadata for
        :param metadata: job new metadata
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting metadata for job {job_id}, metadata={metadata}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update=[{"$set": {"metadata": {"$mergeObjects": ["$metadata", metadata]}}}],
            )
            if updated:
                logger.info(f"Job's {job_id} metadata has been updated")
            return updated

    def update_cost_consumed(self, job_id: ID, consumed_resources: list[JobConsumedResource]) -> bool:
        """
        Updates job's metadata

        :param job_id: identifier of a job to update metadata for
        :param consumed_resources: list of consumed paid resources
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting consumed cost for job {job_id}, consumed_resources={consumed_resources}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            job = self.get_by_id(job_id=job_id)
            if not job:
                raise ValueError("Cannot find job")
            if not job.cost:
                raise ValueError("Job cost is not defined")
            consumed_services = [consumed.service for consumed in job.cost.consumed]
            resources_to_update = [
                JobConsumedResourceMapper.forward(c) for c in consumed_resources if c.service not in consumed_services
            ]
            if len(resources_to_update) == 0:
                return False

            updated = job_repo.update(
                job_id=job_id,
                update={"$push": {"cost.consumed": {"$each": resources_to_update}}},
            )
            if updated:
                logger.info(f"Job's {job_id} consumed cost has been updated")
            return updated

    def set_cost_reported(self, job_id: ID) -> bool:
        """
        Marks job's cost as reported

        :param job_id: identifier of a job to update metadata for
        :return bool: True if job document has been updated
        """
        logger.debug("Setting job's cost as reported")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(job_id=job_id, update={"$set": {"cost.reported": True}})
            if updated:
                logger.info(f"Job's {job_id} cost has been marked as reported")
            return updated

    def set_gpu_state_released(self, job_id: ID) -> bool:
        """
        Sets job's GPU request state to RELEASED

        :param job_id: identifier of a job to update GPU request state for
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting GPU request state to RELEASED for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update=[{"$set": {"gpu.state": JobGpuRequestState.RELEASED.value}}],
            )
            if updated:
                logger.info(f"Job's {job_id} GPU request state has been updated")
            return updated

    #################################################################################
    # Finish                                                                        #
    #################################################################################

    def set_and_publish_finished_state(self, job_id: ID) -> bool:
        """
        Updates job's state to FINISHED and sets end time
        Publish on_job_finished kafka event if job document has been updated

        :param job_id: identifier of a job to update state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting a finished state for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        end_time = now()
        with job_repo._mongo_client.start_session():
            job = self.get_by_id(job_id)
            if job is None:
                raise RuntimeError(f"Job {job_id} cannot be found")
            update_set = {
                "state": JobState.FINISHED.value,
                "state_group": JobStateGroup.FINISHED.value,
                "end_time": end_time,
            }
            if job.gpu is not None and job.gpu.state == JobGpuRequestState.RESERVED:
                update_set["gpu.state"] = JobGpuRequestState.RELEASED.value
            updated = job_repo.update(job_id=job_id, update={"$set": update_set})
        if updated:
            logger.info(f"Job {job_id} has been set to finished state")
            session = CTX_SESSION_VAR.get()
            body = {
                "workspace_id": str(session.workspace_id),
                "job_type": job.type,
                "job_payload": job.payload,
                "job_metadata": job.metadata,
                "start_time": job.start_time.isoformat(),  # type: ignore
                "end_time": end_time.isoformat(),
            }
            publish_event(
                topic="on_job_finished",
                body=body,
                key=str(job.id).encode(),
                headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
            )
        return updated

    #################################################################################
    # Revert                                                                        #
    #################################################################################

    def set_ready_for_revert_state(self, job_id: ID) -> bool:
        """
        Updates job's state to READY_FOR_REVERT
        :param job_id: identifier of a job to update state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting a ready for revert state for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": JobState.READY_FOR_REVERT.value,
                        "executions.revert": {},
                    },
                },
            )
            if updated:
                logger.info(f"Job {job_id} has been set to ready for revert state")
            return updated

    def find_and_lock_job_for_reverting(self) -> Job | None:
        """
        Finds one job for reverting and updates its state to REVERT_SCHEDULING together with filling process_start_time

        This method operates jobs for all the organizations!

        :return job if it's found, None otherwise
        """
        logger.debug("Finding and locking a job for reverting")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            document = job_repo._collection.find_one_and_update(
                filter={
                    "state": JobState.READY_FOR_REVERT.value,
                },
                update={
                    "$set": {
                        "state": JobState.REVERT_SCHEDULING.value,
                        "executions.revert.process_start_time": now(),
                    }
                },
                upsert=False,
                return_document=ReturnDocument.AFTER,
            )
            return None if document is None else JobMapper.backward(document)

    def reset_revert_scheduling_jobs(self, threshold: datetime) -> int:
        """
        Resets all REVERT_SCHEDULING jobs which are older than specified threshold back to READY_FOR_REVERT state
        and increments start_retry_counter

        This method operates jobs for all the organizations!

        :param threshold: process_start_time reset threshold
        :return int: number of jobs modified
        """
        logger.debug(f"Resetting revert scheduling jobs which are older than {threshold}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            count = job_repo._collection.update_many(
                filter={
                    "state": JobState.REVERT_SCHEDULING.value,
                    "executions.revert.process_start_time": {"$lt": threshold},
                },
                update={
                    "$set": {
                        "state": JobState.READY_FOR_REVERT.value,
                    },
                    "$unset": {
                        "executions.revert.process_start_time": "",
                    },
                    "$inc": {
                        "executions.revert.start_retry_counter": 1,
                    },
                },
            ).modified_count
            if count > 0:
                logger.warning(f"Number of revert scheduling jobs which were reset={count}")
            return count

    def reset_revert_scheduling_job(self, job_id: ID) -> bool:
        """
        Resets REVERT_SCHEDULING job by its ID and increments start_retry_counter
        :param job_id: identifier of a job to reset state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Resetting a revert scheduling job {job_id} to ready for revert state")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": JobState.READY_FOR_REVERT.value,
                    },
                    "$unset": {
                        "executions.revert.process_start_time": "",
                    },
                    "$inc": {
                        "executions.revert.start_retry_counter": 1,
                    },
                },
            )
            if updated:
                logger.info(f"A revert scheduling job {job_id} has been reset to ready for revert state")
            return updated

    def set_revert_scheduled_state(
        self,
        job_id: ID,
        flyte_execution_id: str,
    ) -> bool:
        """
        Updates job's state to REVERT_SCHEDULED and sets execution ID
        :param job_id: identifier of a job to update state
        :param flyte_execution_id: Flyte revert execution ID
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting a revert scheduled state for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": JobState.REVERT_SCHEDULED.value,
                        "executions.revert.execution_id": flyte_execution_id,
                    },
                    "$unset": {"executions.revert.process_start_time": ""},
                },
            )
            if updated:
                logger.info(f"Job {job_id} has been set to revert scheduled state")
            return updated

    def set_revert_running_state(self, job_id: ID) -> bool:
        """
        Updates job's state to REVERT_RUNNING
        :param job_id: identifier of a job to update state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting a revert running state for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": JobState.REVERT_RUNNING.value,
                    }
                },
            )
            if updated:
                logger.info(f"Job {job_id} has been set to revert running state")
            return updated

    #################################################################################
    # Failure                                                                       #
    #################################################################################

    def set_and_publish_failed_state(self, job_id: ID) -> bool:
        """
        Updates job's state to FAILED and sets end time
        Publish on_job_failed kafka event if job document has been updated

        :param job_id: identifier of a job to update state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting failed state for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        end_time = now()
        with job_repo._mongo_client.start_session():
            job = self.get_by_id(job_id)
            if job is None:
                raise RuntimeError(f"Job {job_id} cannot be found")
            update_set = {
                "state": JobState.FAILED.value,
                "state_group": JobStateGroup.FAILED.value,
                "end_time": end_time,
            }
            # When a job fails, it must not have "running" tasks
            for i, step in enumerate(job.step_details):
                if step.state == JobTaskState.RUNNING:
                    update_set[f"step_details.{i}.state"] = JobTaskState.FINISHED.value
            if job.gpu is not None and job.gpu.state == JobGpuRequestState.RESERVED:
                update_set["gpu.state"] = JobGpuRequestState.RELEASED.value
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": update_set,
                    "$unset": {
                        "executions.main.process_start_time": "",
                        "executions.revert.process_start_time": "",
                    },
                },
            )
        if updated:
            logger.info(f"Job {job_id} has been set to failed state")
            session = CTX_SESSION_VAR.get()
            body = {
                "workspace_id": str(session.workspace_id),
                "job_type": job.type,
                "job_payload": job.payload,
                "job_metadata": job.metadata,
                "start_time": job.start_time.isoformat() if job.start_time is not None else None,
                "end_time": end_time.isoformat(),
            }
            publish_event(
                topic="on_job_failed",
                body=body,
                key=str(job.id).encode(),
                headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
            )
        return updated

    #################################################################################
    # Cancellation                                                                  #
    #################################################################################

    def get_job_to_delete(self) -> Job | None:
        """
        Finds FINISHED, FAILED or CANCELLED job with cancelled and delete_job flags.
        If job has cost defined, then it will be returned only if cost is marked as reported.

        This method operates jobs for all the organizations!

        :return job if it's found, None otherwise
        """
        logger.debug("Getting a job to delete")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            document = job_repo._collection.find_one(
                filter={
                    "$and": [
                        {
                            "$or": [
                                {"state": JobState.FINISHED.value},
                                {"state": JobState.FAILED.value},
                                {"state": JobState.CANCELLED.value},
                            ],
                        },
                        {"cancellation_info.delete_job": True},
                        {
                            "$or": [
                                {"cost": {"$exists": False}},
                                {"cost.reported": True},
                            ]
                        },
                    ]
                },
            )
            return None if document is None else JobMapper.backward(document)

    def get_cancelled_job(self, job_states: tuple[JobState, ...] | None = None) -> Job | None:
        """
        Finds job with cancelled flag where job state is one from job_states (if specified)

        This method operates jobs for all the organizations!

        :param job_states: job states to check for, optional
        :return job if it's found, None otherwise
        """
        logger.debug("Getting a cancelled job with submitted state")
        job_repo = SessionBasedSchedulerJobRepo()
        filter: dict[str, Any] = {"cancellation_info.is_cancelled": True}
        if job_states is not None:
            filter["state"] = {"$in": [state.value for state in job_states]}
        with job_repo._mongo_client.start_session():
            document = job_repo._collection.find_one(filter=filter)
            return None if document is None else JobMapper.backward(document)

    def find_and_lock_job_for_canceling(self) -> Job | None:
        """
        Finds one job for canceling and updates its state to CANCELING together with filling process_start_time.
        Job for canceling might be only in one of the following states: SCHEDULED, RUNNING

        This method operates jobs for all the organizations!

        :return job if it's found, None otherwise
        """
        logger.debug("Finding and locking a job for cancelling")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            document = job_repo._collection.find_one_and_update(
                filter={
                    "$or": [
                        {"state": JobState.SCHEDULED.value},
                        {"state": JobState.RUNNING.value},
                    ],
                    "cancellation_info.is_cancelled": True,
                },
                update={
                    "$set": {
                        "state": JobState.CANCELING.value,
                        # Do not update state group here, because in CANCELING state job should belong to the original
                        # state group: if it was SCHEDULED it should remain in SCHEDULED group, if it was already
                        # RUNNING it should remain in RUNNING group
                        "executions.main.process_start_time": now(),
                    }
                },
                upsert=False,
                return_document=ReturnDocument.AFTER,
            )
            return None if document is None else JobMapper.backward(document)

    def reset_canceling_jobs(self, threshold: datetime) -> int:
        """
        Resets all CANCELING jobs which are older than specified threshold back either to RUNNING or to SCHEDULED state
        depending on state_group, and increments cancel_retry_counter

        This method operates jobs for all the organizations!

        :param threshold: process_start_time reset threshold
        :return int: number of jobs modified
        """
        logger.debug(f"Resetting canceling jobs which are older than {threshold}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            scheduled_count = job_repo._collection.update_many(
                filter={
                    "state": JobState.CANCELING.value,
                    "state_group": JobStateGroup.SCHEDULED.value,
                    "executions.main.process_start_time": {"$lt": threshold},
                },
                update={
                    "$set": {
                        "state": JobState.SCHEDULED.value,
                    },
                    "$unset": {"executions.main.process_start_time": ""},
                    "$inc": {"executions.main.cancel_retry_counter": 1},
                },
            ).modified_count
            if scheduled_count > 0:
                logger.warning(f"Number of scheduled canceling jobs which were reset={scheduled_count}")
            running_count = job_repo._collection.update_many(
                filter={
                    "state": JobState.CANCELING.value,
                    "state_group": JobStateGroup.RUNNING.value,
                    "executions.main.process_start_time": {"$lt": threshold},
                },
                update={
                    "$set": {
                        "state": JobState.RUNNING.value,
                    },
                    "$unset": {"executions.main.process_start_time": ""},
                    "$inc": {"executions.main.cancel_retry_counter": 1},
                },
            ).modified_count
            if running_count > 0:
                logger.warning(f"Number of scheduled running jobs which were reset={scheduled_count}")
        return scheduled_count + running_count

    def reset_canceling_job(self, job_id: ID) -> bool:
        """
        Resets CANCELING job back to either RUNNING or SCHEDULED by its ID and increments cancel_retry_counter
        :param job_id: identifier of a job to reset state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Resetting a canceling job {job_id} to running or scheduled state")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            job = job_repo.get_document_by_id(job_id)
            if job is None:
                logger.warning(f"Job with id {job_id} has not been found.")
                return False

            orig_state = JobState.RUNNING if job["state_group"] == JobStateGroup.RUNNING.value else JobState.SCHEDULED
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": orig_state.value,
                    },
                    "$unset": {"executions.main.process_start_time": ""},
                    "$inc": {"executions.main.cancel_retry_counter": 1},
                },
            )
            if updated:
                logger.info(f"A canceling job {job_id} has been reset to running or scheduled state")
            return updated

    def drop_cancelled_flag(self, job_id: ID) -> bool:
        """
        Returns CANCELING job back to either RUNNING or SCHEDULED after maximum number of failed canceling attempts
        :param job_id: identifier of a job to reset state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Dropping a cancelled flag for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            job = job_repo.get_document_by_id(job_id)
            if job is None:
                logger.warning(f"Job with id {job_id} has not been found.")
                return False

            orig_state = JobState.RUNNING if job["state_group"] == JobStateGroup.RUNNING.value else JobState.SCHEDULED
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": orig_state.value,
                        "cancellation_info.is_cancelled": False,
                    },
                    "$unset": {
                        "executions.main.process_start_time": "",
                        "executions.main.cancel_retry_counter": "",
                    },
                },
            )
            if updated:
                logger.info(f"A cancelled flag has been dropped for job {job_id}")
            return updated

    def set_and_publish_cancelled_state(self, job_id: ID) -> bool:
        """
        Updates job's state to CANCELLED and sets cancel time
        Publish on_job_cancelled kafka event if job document has been updated

        :param job_id: identifier of a job to update state
        :return bool: True if job document has been updated
        """
        logger.debug(f"Setting cancelled state for job {job_id}")
        job_repo = SessionBasedSchedulerJobRepo()
        cancel_time = now()
        with job_repo._mongo_client.start_session():
            job = self.get_by_id(job_id)
            if job is None:
                raise RuntimeError(f"Job {job_id} cannot be found")
            update_set = {
                "state": JobState.CANCELLED.value,
                "state_group": JobStateGroup.CANCELLED.value,
                "cancellation_info.cancel_time": cancel_time,
                "step_details.$[waitingtask].state": JobTaskState.CANCELLED.value,
                "step_details.$[runningtask].state": JobTaskState.CANCELLED.value,
            }
            if job.gpu is not None and job.gpu.state == JobGpuRequestState.RESERVED:
                update_set["gpu.state"] = JobGpuRequestState.RELEASED.value
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": update_set,
                    "$unset": {
                        "executions.main.process_start_time": "",
                        "executions.revert.process_start_time": "",
                    },
                },
                array_filters=[
                    {"waitingtask.state": JobTaskState.WAITING.value},
                    {"runningtask.state": JobTaskState.RUNNING.value},
                ],
            )
        if updated:
            logger.info(f"Job {job_id} has been set to cancelled state")
            session = CTX_SESSION_VAR.get()
            body = {
                "workspace_id": str(session.workspace_id),
                "job_type": job.type,
                "job_payload": job.payload,
                "job_metadata": job.metadata,
                "start_time": job.start_time.isoformat() if job.start_time is not None else None,
                "cancel_time": cancel_time.isoformat(),
            }
            publish_event(
                topic="on_job_cancelled",
                body=body,
                key=str(job.id).encode(),
                headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
            )
        return updated

    #################################################################################
    # Recovery                                                                      #
    #################################################################################

    def get_scheduled_jobs_not_in_final_state(self) -> tuple[Job, ...]:
        """
        Returns a list of active jobs - jobs which have Flyte executions scheduled and not yet finished
        :return found job or None
        """
        logger.debug("Getting scheduled jobs not in final states")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            documents = job_repo.aggregate_read(
                [
                    {
                        "$match": {
                            "$and": [
                                {"state": {"$gte": JobState.SCHEDULED.value}},
                                {"state": {"$lt": JobState.FINISHED.value}},
                            ],
                        }
                    }
                ]
            )
            return tuple(JobMapper().backward(document) for document in documents)

    def reset_job_to_submitted_state(self, job_id: ID) -> bool:
        """
        Returns a job by its ID
        :param job_id: job ID
        :return bool: True if job document has been updated
        """
        logger.debug(f"Resetting job {job_id} to submitted state")
        job_repo = SessionBasedSchedulerJobRepo()
        with job_repo._mongo_client.start_session():
            updated = job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "state": JobState.SUBMITTED.value,
                        "state_group": JobStateGroup.SCHEDULED.value,
                        "step_details": [],
                        "executions": {"main": {}},
                    },
                },
            )
            if updated:
                logger.info(f"Job {job_id} has been reset to submitted state")
            return updated
