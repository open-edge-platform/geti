# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from contextlib import nullcontext as does_not_raise
from unittest.mock import patch

import pytest

from communication.exceptions import TaskNotFoundException
from entities import TrainingConfig

from geti_fastapi_tools.exceptions import BodyMissingRequiredParameters


@pytest.fixture
def fxt_task_training_config_no_model_template(fxt_project_with_detection_task):
    yield {
        "task_id": fxt_project_with_detection_task.get_trainable_task_nodes()[0].id_,
        "train_from_scratch": True,
    }


@pytest.fixture
def fxt_task_training_config_with_model_template(fxt_project_with_detection_task):
    yield {
        "task_id": fxt_project_with_detection_task.get_trainable_task_nodes()[0].id_,
        "model_template_id": "SSD",
    }


@pytest.fixture
def fxt_task_training_config_invalid_task_id(fxt_task_chain_project):
    yield {"task_id": fxt_task_chain_project.tasks[1].id_}


@pytest.fixture
def fxt_task_training_config_no_task_id():
    yield {"train_from_scratch": True, "model_template_id": "SSD"}


class TestTrainingConfig:
    @pytest.mark.parametrize(
        "training_config_dict, project_fxt, expected_exception, expected_model_template_id",
        [
            (
                "fxt_task_training_config_no_model_template",
                "fxt_project_with_detection_task",
                does_not_raise(),
                "test_template_detection",
            ),
            (
                "fxt_task_training_config_with_model_template",
                "fxt_project_with_detection_task",
                does_not_raise(),
                "SSD",
            ),
            (
                "fxt_task_training_config_invalid_task_id",
                "fxt_task_chain_project",
                pytest.raises(TaskNotFoundException),
                None,
            ),
            (
                "fxt_task_training_config_no_task_id",
                "fxt_task_chain_project",
                pytest.raises(BodyMissingRequiredParameters),
                None,
            ),
            (
                "fxt_task_training_config_no_task_id",
                "fxt_project_with_detection_task",
                does_not_raise(),
                "SSD",
            ),
        ],
        ids=[
            "valid_config_default_model",
            "valid_config_model_template_id",
            "invalid_task_id",
            "no_task_id_in_multitask_project",
            "no_task_id_in_singletask_project",
        ],
    )
    def test_generate_training_config(
        self,
        request,
        training_config_dict,
        project_fxt,
        expected_exception,
        expected_model_template_id,
    ):
        # Arrange
        training_cfg = request.getfixturevalue(training_config_dict)
        project = request.getfixturevalue(project_fxt)

        # Act
        with (
            expected_exception,
            patch.object(
                TrainingConfig,
                "_get_active_model_template_id_for_task",
                return_value=expected_model_template_id,
            ),
        ):
            training_config = TrainingConfig.generate_training_config(project=project, train_config_dict=training_cfg)

        # Assert
        if expected_model_template_id is not None:
            assert training_config.model_template_id == expected_model_template_id
