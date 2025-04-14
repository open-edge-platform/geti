# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
import pathlib
from unittest.mock import patch

import pytest
from geti_types import CTX_SESSION_VAR, ID, make_session
from jobs_common.k8s_helpers.k8s_resources_calculation import ComputeResources, EphemeralStorageResources
from jobs_common.k8s_helpers.trainer_image_info import TrainerImageInfo
from sc_sdk.entities.compiled_dataset_shards import (
    CompiledDatasetShard,
    CompiledDatasetShards,
    NullCompiledDatasetShards,
)

from job.models import OptimizationTrainerContext

CTX_SESSION_VAR.set(make_session())


def detect_fixtures(module_name: str) -> list:
    """
    Searches for fixtures at given path provided in python module notation,
    starting on current working directory.
    :param module_name: name of module where fixtures folder is located
    :return: list of string representing fixture modules/plugins
    """
    fixtures: set = set()
    fixtures_path = pathlib.Path(os.path.dirname(__file__)) / "fixtures"
    for fixture_path in fixtures_path.iterdir():
        if not fixture_path.stem.endswith("__"):
            fixtures.add(".".join([module_name, "fixtures", fixture_path.stem]))
    return list(fixtures)


pytest_plugins = detect_fixtures("tests")


@pytest.fixture()
def fxt_dataset_id(fxt_mongo_id):
    return fxt_mongo_id(1003)


@pytest.fixture
def fxt_label_schema_id(fxt_mongo_id):
    return fxt_mongo_id(14)


@pytest.fixture
def fxt_norm_compiled_dataset_shards(fxt_dataset_id: ID, fxt_label_schema_id: ID) -> CompiledDatasetShards:
    return CompiledDatasetShards(
        dataset_id=fxt_dataset_id,
        label_schema_id=fxt_label_schema_id,
        compiled_shard_files=[
            CompiledDatasetShard(
                filename="dummy.arrow",
                binary_filename="dummy.arrow",
                size=10,
                checksum="asdf",
            )
        ],
    )


@pytest.fixture
def fxt_null_compiled_dataset_shards() -> NullCompiledDatasetShards:
    return NullCompiledDatasetShards()


@pytest.fixture(params=["fxt_norm_compiled_dataset_shards", "fxt_null_compiled_dataset_shards"])
def fxt_compiled_dataset_shards(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def fxt_project(fxt_empty_project, fxt_dataset_storage):
    with patch.object(fxt_empty_project, "get_training_dataset_storage", return_value=fxt_dataset_storage):
        yield fxt_empty_project


@pytest.fixture(autouse=True)
def fxt_requests_post():
    """Patch istio-proxy termination callback not to raise an error in local environment."""
    with patch("jobs_common.tasks.primary_container_task.requests.post") as mock_requests_post:
        mock_requests_post.return_value.status_code = 200
        yield mock_requests_post


@pytest.fixture
def fxt_optimization_trainer_ctx() -> OptimizationTrainerContext:
    with patch("job.models.trainer.ModelRepo", autospec=True):
        return OptimizationTrainerContext(
            workspace_id="workspace_id",
            project_id="project_id",
            job_id="job_id",
            input_model_id="input_model_id",
            model_to_optimize_id="model_to_optimize_id",
            model_storage_id="model_storage_id",
            ephemeral_storage_resources=EphemeralStorageResources(limits=250, requests=100, work_dir_size_limit=10),
            compute_resources=ComputeResources(
                cpu_requests=None,
                cpu_limits=None,
                memory_requests=None,
                memory_limits=None,
                gpu_requests=None,
                gpu_limits=None,
                accelerator_name="nvidia",
            ),
            trainer_image_info=TrainerImageInfo(train_image_name="optimizer", sidecar_image_name="istio"),
        )
