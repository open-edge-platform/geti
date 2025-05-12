# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from entities.project_configuration import (
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
