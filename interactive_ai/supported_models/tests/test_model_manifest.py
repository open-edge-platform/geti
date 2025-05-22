# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
import pathlib
from importlib import resources
from unittest.mock import patch

import hiyapyco
import pytest
from geti_configuration_tools.hyperparameters import (
    AugmentationParameters,
    DatasetPreparationParameters,
    EarlyStopping,
    EvaluationParameters,
    Hyperparameters,
    TrainingHyperParameters,
)

from geti_supported_models import manifests
from geti_supported_models.model_manifest import (
    Capabilities,
    GPUMaker,
    ModelManifest,
    ModelManifestDeprecationStatus,
    ModelStats,
    NullModelManifest,
)
from geti_supported_models.parser import parse_manifest

BASE_MANIFEST_PATH = str(resources.files(manifests).joinpath("base.yaml"))
TEST_PATH = pathlib.Path(os.path.dirname(__file__))
DUMMY_BASE_MANIFEST_PATH = os.path.join(TEST_PATH, "dummy_base_model_manifest.yaml")
DUMMY_MANIFEST_PATH = os.path.join(TEST_PATH, "dummy_model_manifest.yaml")


@pytest.fixture
def fxt_dummy_model_stats():
    yield ModelStats(
        gigaflops=0.39,
        trainable_parameters=5288548,
    )


@pytest.fixture
def fxt_dummy_supported_gpu():
    yield {GPUMaker.INTEL: True, GPUMaker.NVIDIA: True}


@pytest.fixture
def fxt_dummy_hyperparameters():
    yield Hyperparameters(
        dataset_preparation=DatasetPreparationParameters(augmentation=AugmentationParameters()),
        training=TrainingHyperParameters(max_epochs=101, learning_rate=0.05, early_stopping=EarlyStopping(patience=5)),
        evaluation=EvaluationParameters(metric=None),
    )


@pytest.fixture
def fxt_dummy_model_manifest(fxt_dummy_model_stats, fxt_dummy_supported_gpu, fxt_dummy_hyperparameters):
    yield ModelManifest(
        id="dummy_model_manifest",
        name="Dummy ModelManifest",
        description="Dummy manifest for test purposes only",
        task="classification",
        stats=fxt_dummy_model_stats,
        support_status=ModelManifestDeprecationStatus.OBSOLETE,
        supported_gpus=fxt_dummy_supported_gpu,
        hyperparameters=fxt_dummy_hyperparameters,
        capabilities=Capabilities(xai=True, tiling=False),
    )


@pytest.mark.ScSdkComponent
class TestModelManifest:
    """
    Test class for parsing model manifest files.
    """

    def test_dummy_model_manifest_parsing(self, fxt_dummy_model_manifest):
        model_manifest = parse_manifest(
            BASE_MANIFEST_PATH, DUMMY_BASE_MANIFEST_PATH, DUMMY_MANIFEST_PATH, relative=False
        )

        assert model_manifest == fxt_dummy_model_manifest

    def test_relative_path_parsing(self):
        sources = ("base.yaml", "dummy_base_model_manifest.yaml", "dummy_model_manifest.yaml")
        expected_paths = [resources.files(manifests).joinpath(path) for path in sources]

        # Create a more complete mock result with all required nested fields
        mock_yaml_result = {
            "id": "test",
            "name": "Test Model",
            "description": "Test",
            "task": "detection",
            "stats": {"gigaflops": 1.0, "trainable_parameters": 1000},
            "support_status": "active",
            "supported_gpus": {"intel": True},
            "hyperparameters": {
                "dataset_preparation": {
                    "augmentation": {
                        "gaussian_blur": {"kernel_size": 2},
                        "tiling": {"adaptive_tiling": True, "tile_size": 100, "tile_overlap": 50},
                    }
                },
                "training": {"max_epochs": 100, "learning_rate": 0.01, "early_stopping": {"patience": 3}},
                "evaluation": {"metric": None},
            },
            "capabilities": {
                "xai": True,
                "tiling": False,
            },
        }

        with patch("hiyapyco.load") as mock_load:
            mock_load.return_value = mock_yaml_result
            model_manifest = parse_manifest(*sources, relative=True)

            # Verify hiyapyco.load was called with the correct paths
            mock_load.assert_called_once_with(
                *expected_paths, method=hiyapyco.METHOD_MERGE, interpolate=True, failonmissingfiles=True
            )
            assert model_manifest == ModelManifest(**mock_yaml_result)

    def test_null_model_manifest(self):
        null_model_manifest = NullModelManifest()

        assert null_model_manifest.id == "null"
        assert null_model_manifest.support_status == ModelManifestDeprecationStatus.OBSOLETE
        assert null_model_manifest.stats.gigaflops == 1
        assert null_model_manifest.stats.trainable_parameters == 1
        assert null_model_manifest.supported_gpus == {}
        assert null_model_manifest.hyperparameters.dataset_preparation.augmentation == AugmentationParameters()
