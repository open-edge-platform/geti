# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from datetime import datetime

import pytest
from bson import ObjectId
from geti_types import ID
from jobs_common.tasks.utils.secrets import JobMetadata

from job.utils.train_workflow_data import TrainWorkflowData


@pytest.fixture
def fxt_mongo_id():
    """
    Create a realistic MongoDB ID string for testing purposes.

    If you need multiple ones, call this fixture repeatedly with different arguments.
    """
    base_id: int = 0x60D31793D5F1FB7E6E3C1A4F

    def _build_id(offset: int = 0) -> str:
        return str(hex(base_id + offset))[2:]

    yield _build_id


@pytest.fixture
def fxt_ote_id(fxt_mongo_id):
    """
    Create a realistic OTE ID for testing purposes. Based on the fxt_mongo_id, but this
    fixture returns an actual ID entity instead of a string.
    """

    def _build_ote_id(offset: int = 0) -> ID:
        return ID(fxt_mongo_id(offset))

    yield _build_ote_id


@pytest.fixture
def fxt_train_data():
    """
    Get a train data creator with default values
    """

    def _build_train_data(
        workspace_id: str = "workspace_id",
        project_id: str = "project_id",
        task_id: str = "task_id",
        label_schema_id: str = "label_schema_id",
        model_storage_id: str = "model_storage_id",
        hyperparameters_id: str = "hyperparameters_id",
        from_scratch: bool = False,
        should_activate_model: bool = False,
        infer_on_pipeline: bool = False,
        active_model_id: str = "active_model_id",
        input_model_id: str = "input_model_id",
        compiled_dataset_shards_id: str | None = None,
        reshuffle_subsets: bool = False,
    ) -> TrainWorkflowData:
        return TrainWorkflowData(
            workspace_id=workspace_id,
            project_id=project_id,
            task_id=task_id,
            label_schema_id=label_schema_id,
            model_storage_id=model_storage_id,
            hyperparameters_id=hyperparameters_id,
            from_scratch=from_scratch,
            should_activate_model=should_activate_model,
            infer_on_pipeline=infer_on_pipeline,
            active_model_id=active_model_id,
            input_model_id=input_model_id,
            compiled_dataset_shards_id=compiled_dataset_shards_id,
            min_annotation_size=None,
            max_number_of_annotations=None,
            reshuffle_subsets=reshuffle_subsets,
        )

    yield _build_train_data


@pytest.fixture(autouse=True)
def fxt_job_metadata():
    job_id = str(ObjectId())
    job_type = "dummy_job_type"
    job_name = "dummy_job_name"
    job_author = str(ObjectId())
    job_start_time = datetime.now()
    session_env_vars = {
        "JOB_METADATA_ID": job_id,
        "JOB_METADATA_TYPE": job_type,
        "JOB_METADATA_NAME": job_name,
        "JOB_METADATA_AUTHOR": job_author,
        "JOB_METADATA_START_TIME": job_start_time.isoformat(),
    }
    os.environ.update(session_env_vars)

    yield JobMetadata(
        id=job_id,
        type=job_type,
        name=job_name,
        author=job_author,
        start_time=job_start_time,
    )

    for key in session_env_vars:
        os.environ.pop(key)
