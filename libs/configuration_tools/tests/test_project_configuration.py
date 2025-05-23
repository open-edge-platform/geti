# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID

from geti_configuration_tools.project_configuration import (
    AutoTrainingParameters,
    ProjectConfiguration,
    TaskConfig,
    TrainConstraints,
    TrainingParameters,
)


class TestProjectConfiguration:
    @pytest.mark.parametrize(
        "project_config_dict, expected_config",
        [
            (
                {
                    "project_id": ID("test_id_1"),
                    "task_configs": [
                        {
                            "task_id": "task_1",
                            "training": {"constraints": {"min_images_per_label": 10}},
                            "auto_training": {
                                "enable": True,
                                "enable_dynamic_required_annotations": False,
                                "min_images_per_label": 5,
                            },
                        },
                    ],
                },
                ProjectConfiguration(
                    project_id=ID("test_id_1"),
                    task_configs=[
                        TaskConfig(
                            task_id="task_1",
                            training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=10)),
                            auto_training=AutoTrainingParameters(
                                enable=True,
                                enable_dynamic_required_annotations=False,
                                min_images_per_label=5,
                            ),
                        )
                    ],
                ),
            ),
            (
                {
                    "project_id": ID("test_id_2"),
                    "task_configs": [
                        {
                            "task_id": "classification_task",
                            "training": {"constraints": {"min_images_per_label": 20}},
                            "auto_training": {
                                "enable": True,
                                "enable_dynamic_required_annotations": True,
                                "min_images_per_label": 10,
                            },
                        },
                        {
                            "task_id": "detection_task",
                            "training": {"constraints": {"min_images_per_label": 30}},
                            "auto_training": {
                                "enable": False,
                                "enable_dynamic_required_annotations": False,
                                "min_images_per_label": 0,
                            },
                        },
                    ],
                },
                ProjectConfiguration(
                    project_id=ID("test_id_2"),
                    task_configs=[
                        TaskConfig(
                            task_id="classification_task",
                            training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=20)),
                            auto_training=AutoTrainingParameters(
                                enable=True,
                                enable_dynamic_required_annotations=True,
                                min_images_per_label=10,
                            ),
                        ),
                        TaskConfig(
                            task_id="detection_task",
                            training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=30)),
                            auto_training=AutoTrainingParameters(
                                enable=False,
                                enable_dynamic_required_annotations=False,
                                min_images_per_label=0,
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_project_configuration(self, project_config_dict, expected_config):
        # Create configuration from dict
        config = ProjectConfiguration(**project_config_dict)

        # Basic validation
        assert config.project_id == expected_config.project_id
        assert config.task_configs
        assert len(config.task_configs) == len(expected_config.task_configs)

        # Detailed validation
        for i, task_config in enumerate(config.task_configs):
            expected_task_config = expected_config.task_configs[i]

            assert task_config.task_id == expected_task_config.task_id
            assert task_config.training.constraints.min_images_per_label == (
                expected_task_config.training.constraints.min_images_per_label
            )
            assert task_config.auto_training.enable == expected_task_config.auto_training.enable
            assert task_config.auto_training.enable_dynamic_required_annotations == (
                expected_task_config.auto_training.enable_dynamic_required_annotations
            )
            assert task_config.auto_training.min_images_per_label == (
                expected_task_config.auto_training.min_images_per_label
            )
