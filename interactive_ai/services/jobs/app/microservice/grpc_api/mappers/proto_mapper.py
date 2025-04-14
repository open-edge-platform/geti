# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Job to gRPC message module
"""

import json
from datetime import datetime

from model.job import Job

from grpc_interfaces.job_submission.pb.job_service_pb2 import JobResponse


class JobToProto:
    """
    Maps Job to and from protobuf
    """

    @staticmethod
    def forward(instance: Job) -> JobResponse:
        """
        Converts the job instance into a gRPC JobResponse message.

        :param instance: the job instance to convert
        :return: corresponding JobResponse object
        :raises JobAttributeNotSerializableException: if the job attribute is not serializable
        """
        step_details = []
        for job_step_details in instance.step_details:
            step_detail = JobResponse.StepDetails(
                index=job_step_details.index,
                task_id=str(job_step_details.task_id),
                step_name=job_step_details.step_name,
                state=job_step_details.state.name,
                progress=job_step_details.progress if job_step_details.progress is not None else 0,
                message=job_step_details.message if job_step_details.message is not None else "",
                warning=job_step_details.warning if job_step_details.warning is not None else "",
            )
            step_details.append(step_detail)

        project_id = str(instance.project_id) if instance.project_id else ""
        start_time = JobToProto._iso_format_from_datetime(instance.start_time)
        end_time = JobToProto._iso_format_from_datetime(instance.end_time)
        cancellation_info = JobResponse.CancellationInfo(
            is_cancelled=instance.cancellation_info.is_cancelled,
            user_uid=instance.cancellation_info.user_uid if instance.cancellation_info.user_uid is not None else "",
            cancel_time=JobToProto._iso_format_from_datetime(instance.cancellation_info.cancel_time),
            request_time=JobToProto._iso_format_from_datetime(instance.cancellation_info.request_time),
            delete_job=instance.cancellation_info.delete_job,
        )
        cost = (
            JobResponse.JobCost(
                requests=[
                    JobResponse.JobResource(amount=request.amount, unit=request.unit)
                    for request in instance.cost.requests
                ],
                consumed=[
                    JobResponse.JobResource(amount=request.amount, unit=request.unit)
                    for request in instance.cost.consumed
                ],
            )
            if instance.cost is not None
            else None
        )
        try:
            payload = json.dumps(instance.payload)
        except TypeError:
            raise ValueError(f"Unable to serialize job payload for job with ID `{str(instance.id)}`.")
        try:
            metadata = json.dumps(instance.metadata)
        except TypeError:
            raise ValueError(f"Unable to serialize job metadata for job with ID `{str(instance.id)}`.")

        return JobResponse(
            id=str(instance.id),
            workspace_id=str(instance.workspace_id),
            type=instance.type,
            priority=instance.priority,
            job_name=instance.job_name,
            key=instance.key,
            state=instance.state.name,
            state_group=instance.state_group.name,
            step_details=step_details,
            payload=payload,
            metadata=metadata,
            creation_time=instance.creation_time.isoformat(),
            author=instance.author,
            project_id=project_id,
            start_time=start_time,
            end_time=end_time,
            cancellation_info=cancellation_info,
            cost=cost,
        )

    @staticmethod
    def _iso_format_from_datetime(time: datetime | None) -> str:
        """Converts a datetime object into an iso formatted string."""
        return time.isoformat() if time else ""
