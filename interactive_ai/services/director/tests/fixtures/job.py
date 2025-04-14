# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

DUMMY_TRAIN_TASK_JOB_NAME = "test_k8s_train_task_job"
DUMMY_TRAIN_TASK_JOB_DESC = "test_k8s_train_task_desc"
DUMMY_TRAIN_PIPELINE_JOB_NAME = "test_k8s_train_pipeline_job"
DUMMY_TRAIN_PIPELINE_JOB_DESC = "test_k8s_train_pipeline_desc"
DUMMY_OPTIMIZE_JOB_NAME = "test_k8s_optimize_job"
DUMMY_OPTIMIZE_JOB_DESC = "test_k8s_optimize_desc"


def do_nothing(self, *args, **kwargs) -> None:
    return None


@pytest.fixture
def fxt_model_test_job_rest():
    return {
        "id": "62e11d25f690b28c02365059",
        "name": "Model testing",
        "creation_time": "2022-07-27T11:10:29.182000+00:00",
        "type": "test",
        "metadata": {
            "project": {
                "id": "60d31793d5f1fb7e6e3c1a51",
                "name": "dummy_empty_project",
            },
            "task": {"task_id": "60d31793d5f1fb7e6e3c1a59"},
            "test": {
                "model_template_id": "test_template_dataset",
                "model_architecture": "Sample Dataset Template",
                "datasets": [
                    {
                        "id": "60d31793d5f1fb7e6e3c1a52",
                        "name": "dummy_dataset_storage",
                    }
                ],
            },
        },
    }
