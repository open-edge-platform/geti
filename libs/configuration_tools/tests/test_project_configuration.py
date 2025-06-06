# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID

from geti_configuration_tools.project_configuration import (
    AutoTrainingParameters,
    PartialTaskConfig,
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
    def test_project_configuration(self, project_config_dict, expected_config) -> None:
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

    def test_partial_task_config(self) -> None:
        # Test partial model creation
        partial_task_config = PartialTaskConfig.model_validate(
            {
                "task_id": "partial_task",
                "training": {"constraints": {"min_images_per_label": 5}},
            }
        )

        assert partial_task_config.task_id == "partial_task"
        assert partial_task_config.training.constraints.min_images_per_label == 5
        assert partial_task_config.auto_training is None

    def test_get_task_config(self) -> None:
        # Create a project configuration with multiple tasks
        project_config = ProjectConfiguration(
            project_id=ID("test_project"),
            task_configs=[
                TaskConfig(
                    task_id="task_1",
                    training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=10)),
                    auto_training=AutoTrainingParameters(enable=True, min_images_per_label=5),
                ),
                TaskConfig(
                    task_id="task_2",
                    training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=20)),
                    auto_training=AutoTrainingParameters(enable=False, min_images_per_label=0),
                ),
            ],
        )

        # Test retrieving a valid task config
        task_config = project_config.get_task_config("task_1")
        assert task_config is not None
        assert task_config.task_id == "task_1"
        assert task_config.training.constraints.min_images_per_label == 10
        assert task_config.auto_training.enable is True
        assert task_config.auto_training.min_images_per_label == 5

        # Test retrieving another valid task config
        task_config = project_config.get_task_config("task_2")
        assert task_config is not None
        assert task_config.task_id == "task_2"
        assert task_config.training.constraints.min_images_per_label == 20
        assert task_config.auto_training.enable is False

        # Test retrieving a non-existent task config
        with pytest.raises(ValueError, match="Task configuration with ID non_existent_task not found"):
            project_config.get_task_config("non_existent_task")

    def test_update_task_config(self) -> None:
        # Create a project configuration with a task
        project_config = ProjectConfiguration(
            project_id=ID("test_project"),
            task_configs=[
                TaskConfig(
                    task_id="task_1",
                    training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=10)),
                    auto_training=AutoTrainingParameters(enable=True, min_images_per_label=5),
                ),
            ],
        )

        # Create updated task config
        updated_task_config = TaskConfig(
            task_id="task_1",
            training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=20)),
            auto_training=AutoTrainingParameters(
                enable=False, enable_dynamic_required_annotations=True, min_images_per_label=15
            ),
        )

        # Update the task config
        project_config.update_task_config(updated_task_config)

        # Verify the task config was updated
        task_config = project_config.get_task_config("task_1")
        assert task_config.training.constraints.min_images_per_label == 20
        assert task_config.auto_training.enable is False
        assert task_config.auto_training.enable_dynamic_required_annotations is True
        assert task_config.auto_training.min_images_per_label == 15

        # Test updating a non-existent task config
        non_existent_task = TaskConfig(
            task_id="non_existent_task",
            training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=5)),
            auto_training=AutoTrainingParameters(enable=True, min_images_per_label=2),
        )

        with pytest.raises(ValueError, match="Task configuration with ID non_existent_task not found"):
            project_config.update_task_config(non_existent_task)
