# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
import pathlib

import pytest

from sc_sdk.algorithms import (
    Algorithm,
    AlgorithmStats,
    AugmentationParameters,
    DatasetPreparationParameters,
    EvaluationParameters,
    Hyperparameters,
    NullAlgorithm,
    SupportedStatus,
    TrainingHyperParameters,
)
from sc_sdk.algorithms.utils import MODEL_MANIFEST_PATH, parse_manifest

BASE_MANIFEST_PATH = os.path.join(MODEL_MANIFEST_PATH, "base.yaml")
TEST_PATH = pathlib.Path(os.path.dirname(__file__))
DUMMY_BASE_MANIFEST_PATH = os.path.join(TEST_PATH, "dummy_base_model_manifest.yaml")
DUMMY_MANIFEST_PATH = os.path.join(TEST_PATH, "dummy_model_manifest.yaml")


@pytest.fixture
def fxt_dummy_algorithm_stats():
    yield AlgorithmStats(
        gigaflops=0.39,
        trainable_parameters=5288548,
    )


@pytest.fixture
def fxt_dummy_algorithm_supported_gpu():
    yield {"intel": True, "nvidia": True}


@pytest.fixture
def fxt_dummy_algorithm_hyperparameters():
    yield Hyperparameters(
        dataset_preparation=DatasetPreparationParameters(
            augmentation=AugmentationParameters(
                horizontal_flip=True, vertical_flip=False, gaussian_blur=False, random_rotate=True
            )
        ),
        training=TrainingHyperParameters(
            max_epochs=100, early_stopping_epochs=4, learning_rate=0.05, learning_rate_warmup_epochs=4, batch_size=32
        ),
        evaluation=EvaluationParameters(metric=None),
    )


@pytest.fixture
def fxt_dummy_algorithm(
    fxt_dummy_algorithm_stats, fxt_dummy_algorithm_supported_gpu, fxt_dummy_algorithm_hyperparameters
):
    yield Algorithm(
        id="dummy_algorithm",
        name="Dummy Algorithm",
        description="Dummy manifest for test purposes only",
        task="classification",
        stats=fxt_dummy_algorithm_stats,
        support_status=SupportedStatus.OBSOLETE,
        supported_gpus=fxt_dummy_algorithm_supported_gpu,
        hyperparameters=fxt_dummy_algorithm_hyperparameters,
    )


@pytest.mark.ScSdkComponent
class TestAlgorithm:
    """
    Test class for parsing model manifest files.
    """

    def test_dummy_model_manifest_parsing(self, fxt_dummy_algorithm):
        algorithm = parse_manifest(BASE_MANIFEST_PATH, DUMMY_BASE_MANIFEST_PATH, DUMMY_MANIFEST_PATH)

        assert algorithm == fxt_dummy_algorithm

    def test_null_algorithm(self):
        null_algorithm = NullAlgorithm()

        assert null_algorithm.id == "null"
        assert null_algorithm.support_status == SupportedStatus.OBSOLETE
        assert null_algorithm.stats.gigaflops == 1
        assert null_algorithm.stats.trainable_parameters == 1
        assert null_algorithm.supported_gpus == {}
        assert null_algorithm.hyperparameters.dataset_preparation.augmentation == AugmentationParameters(
            horizontal_flip=False,
            vertical_flip=False,
            gaussian_blur=False,
            random_rotate=False,
        )
