# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from geti_supported_models.hyperparameters import (
    Hyperparameters,
    AugmentationParameters,
    CenterCrop,
    DatasetPreparationParameters,
    TrainingHyperParameters,
    EvaluationParameters
)
from entities.training_configuration import (
    TrainingConfiguration,
    GlobalParameters,
    GlobalDatasetPreparationParameters,
    SubsetSplit,
    Filtering
)


@pytest.fixture
def ftx_hyperparameters():
    yield Hyperparameters(
        dataset_preparation=DatasetPreparationParameters(
            augmentation=AugmentationParameters(
                center_crop=CenterCrop(ratio=0.6),
            )
        ),
        training=TrainingHyperParameters(
            max_epochs=100,
            early_stopping_epochs=10,
            learning_rate=0.001,
            learning_rate_warmup_epochs=5,
            batch_size=32,
        ),
        evaluation=EvaluationParameters(),
    )

@pytest.fixture
def fxt_global_parameters():
    yield GlobalParameters(
        dataset_preparation=GlobalDatasetPreparationParameters(
            subset_split=SubsetSplit(
                training=70,
                validation=20,
                test=10,
                auto_selection=True,
                remixing=False,
            ),
            filtering=Filtering(
                min_annotation_pixels=10,
                max_annotation_pixels=1000,
                max_annotation_objects=100,
            )
        )
    )


@pytest.fixture
def fxt_training_configuration(fxt_mongo_id, fxt_global_parameters, ftx_hyperparameters):
    yield TrainingConfiguration(
        id_=fxt_mongo_id(11),
        task_id=fxt_mongo_id(22),
        model_manifest_id="test_model_manifest_id",
        global_parameters=fxt_global_parameters,
        hyperparameters=ftx_hyperparameters,
    )
