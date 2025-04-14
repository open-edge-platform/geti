# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from model.job import Job


def assert_jobs_equal_deep(job1: Job, job2: Job) -> None:
    assert (
        job1.id == job2.id
        and job1.workspace_id == job2.workspace_id
        and job1.type == job2.type
        and job1.priority == job2.priority
        and job1.job_name == job2.job_name
        and job1.key == job2.key
        and job1.state == job2.state
        and job1.state_group == job2.state_group
        and job1.step_details == job2.step_details
        and job1.payload == job2.payload
        and job1.metadata == job2.metadata
        and job1.creation_time == job2.creation_time
        and job1.author == job2.author
        and job1.project_id == job2.project_id
        and job1.start_time == job2.start_time
        and job1.end_time == job2.end_time
        and job1.cancellation_info == job2.cancellation_info
        and job1.executions == job2.executions
        and job1.session.as_json() == job2.session.as_json()
        and job1.telemetry == job2.telemetry
        and job1.gpu == job2.gpu
        and job1.cost == job2.cost
    )
