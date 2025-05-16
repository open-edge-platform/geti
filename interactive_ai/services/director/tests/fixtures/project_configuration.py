# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_configuration_tools.project_configuration import (
    AutoTrainingParameters,
    ProjectConfiguration,
    TaskConfig,
    TrainConstraints,
    TrainingParameters,
)


@pytest.fixture
def fxt_project_configuration(fxt_project_identifier):
    yield ProjectConfiguration(
        project_id=fxt_project_identifier.project_id,
        task_configs=[
            TaskConfig(
                task_id="task_1",
                training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=10)),
                auto_training=AutoTrainingParameters(
                    enable=True,
                    enable_dynamic_required_annotations=False,
                    min_images_per_label=5,
                ),
            ),
            TaskConfig(
                task_id="task_2",
                training=TrainingParameters(constraints=TrainConstraints(min_images_per_label=15)),
                auto_training=AutoTrainingParameters(
                    enable=False,
                    enable_dynamic_required_annotations=True,
                    min_images_per_label=8,
                ),
            ),
        ],
    )


@pytest.fixture
def fxt_project_configuration_rest_view(fxt_project_configuration):    
    tasks_rest_view = []
    for task_config in fxt_project_configuration.task_configs:
        min_images_per_label_schema = (
            task_config.training.constraints.model_json_schema()["properties"]["min_images_per_label"]
        )
        auto_training_schema = task_config.auto_training.model_json_schema()
        tasks_rest_view.append(
            {
                "task_id": task_config.task_id,
                "training": {
                    "constraints": [
                        {
                            "key": "min_images_per_label",
                            "name": min_images_per_label_schema["title"],
                            "description": min_images_per_label_schema["description"],
                            "type": "int",
                            "value": task_config.training.constraints.min_images_per_label,
                            "default_value": min_images_per_label_schema["default"],
                            "max_value": min_images_per_label_schema.get("maximum"),
                            "min_value": min_images_per_label_schema.get("minimum"),
                        }
                    ]
                },
                "auto_training": [
                    {
                        "key": "enable",
                        "name": auto_training_schema["properties"]["enable"]["title"],
                        "description": auto_training_schema["properties"]["enable"]["description"],
                        "type": "bool",
                        "value": task_config.auto_training.enable,
                        "default_value": auto_training_schema["properties"]["enable"]["default"],
                    },
                    {
                        "key": "enable_dynamic_required_annotations",
                        "name": auto_training_schema["properties"]["enable_dynamic_required_annotations"]["title"],
                        "description": (
                            auto_training_schema["properties"]["enable_dynamic_required_annotations"]["description"]
                        ),
                        "type": "bool",
                        "value": task_config.auto_training.enable_dynamic_required_annotations,
                        "default_value": (
                            auto_training_schema["properties"]["enable_dynamic_required_annotations"]["default"]
                        ),
                    },
                    {
                        "key": "min_images_per_label",
                        "name": auto_training_schema["properties"]["min_images_per_label"]["title"],
                        "description": auto_training_schema["properties"]["min_images_per_label"]["description"],
                        "type": "int",
                        "value": task_config.auto_training.min_images_per_label,
                        "default_value": auto_training_schema["properties"]["min_images_per_label"]["default"],
                        "max_value": None,
                        "min_value": 0,
                    }
                ]
            }
        )
    yield {
        "task_configs": tasks_rest_view
    }
