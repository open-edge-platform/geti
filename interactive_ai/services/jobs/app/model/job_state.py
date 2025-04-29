# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Job states module
"""

from enum import Enum


class JobState(Enum):
    """
    Job states enumeration
    Represents the state of the whole submitted job

    Initial state:
    SUBMITTED                       job is persisted in MongoDB, there is a running duplicate, waiting

    Intermediate states:
    READY_FOR_SCHEDULING            job is persisted in MongoDB, no running duplicates, ready to be picked for
                                    scheduling
    SCHEDULING                      job is picked by scheduler, Flyte execution is being created
    SCHEDULED                       Flyte execution is created but not started yet
    RUNNING                         Flyte execution is started

    CANCELING                       job is picked by scheduler, Flyte execution is being canceling

    READY_FOR_REVERT                job main execution has been cancelled or has failed, ready for reverting
    REVERT_SCHEDULING               job is picked by scheduler, Flyte revert execution is being created
    REVERT_SCHEDULED                Flyte revert execution is created but not started yet
    REVERT_RUNNING                  Flyte revert execution is started

    Final states:
    FINISHED                        Flyte execution is finished successfully
    FAILED                          Flyte execution failed
    CANCELLED                       Flyte execution is cancelled
    """

    SUBMITTED = 0

    READY_FOR_SCHEDULING = 1
    SCHEDULING = 2
    SCHEDULED = 3
    RUNNING = 4

    CANCELING = 5

    READY_FOR_REVERT = 6
    REVERT_SCHEDULING = 7
    REVERT_SCHEDULED = 8
    REVERT_RUNNING = 9

    FINISHED = 100
    FAILED = 101
    CANCELLED = 102


class JobStateGroup(Enum):
    """
    Job state groups enumeration
    Represents the state group of the job, it matches with UI job states
    """

    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobTaskState(Enum):
    """
    Job task state enumeration
    Represents the state of one single task within a job

    WAITING             task is waiting to be executed
    RUNNING             task is being executed
    FINISHED            task is finished successfully
    FAILED              task failed
    CANCELLED           task execution is cancelled
    SKIPPED             task execution is skipped (for conditionals)

    """

    WAITING = "WAITING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class JobGpuRequestState(Enum):
    """
    Job GPU request state enumeration
    Represents the state of GPU request

    WAITING             GPU is to be reserved
    RESERVED            GPU is reserved
    RELEASED            GPU is released

    """

    WAITING = "WAITING"
    RESERVED = "RESERVED"
    RELEASED = "RELEASED"
