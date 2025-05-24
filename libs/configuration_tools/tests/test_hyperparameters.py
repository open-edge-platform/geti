# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from pydantic import ValidationError

from geti_configuration_tools.hyperparameters import (
    AugmentationParameters,
    CenterCrop,
    DatasetPreparationParameters,
    EarlyStopping,
    EvaluationParameters,
    GaussianBlur,
    Hyperparameters,
    MaxDetectionPerImage,
    PartialHyperparameters,
    RandomAffine,
    RandomHorizontalFlip,
    RandomResizeCrop,
    Tiling,
    TrainingHyperParameters,
)


class TestHyperparameters:
    @pytest.mark.parametrize(
        "hyperparams_dict, expected_params",
        [
            # Test case 1: Basic configuration
            (
                {
                    "dataset_preparation": {"augmentation": {"random_horizontal_flip": {"enable": True}}},
                    "training": {"max_epochs": 50, "learning_rate": 0.01},
                    "evaluation": {},
                },
                Hyperparameters(
                    dataset_preparation=DatasetPreparationParameters(
                        augmentation=AugmentationParameters(random_horizontal_flip=RandomHorizontalFlip(enable=True))
                    ),
                    training=TrainingHyperParameters(max_epochs=50, learning_rate=0.01),
                    evaluation=EvaluationParameters(),
                ),
            ),
            # Test case 2: Complex configuration with all augmentation options
            (
                {
                    "dataset_preparation": {
                        "augmentation": {
                            "center_crop": {"enable": True, "ratio": 0.8},
                            "random_resize_crop": {"enable": True, "ratio": 0.5},
                            "random_affine": {
                                "enable": True,
                                "degrees": 30,
                                "translate_x": 0.1,
                                "translate_y": 0.1,
                                "scale": 0.9,
                            },
                            "random_horizontal_flip": {"enable": True},
                            "gaussian_blur": {"enable": True, "kernel_size": 3},
                            "tiling": {"enable": True, "adaptive_tiling": True, "tile_size": 224, "tile_overlap": 32},
                        }
                    },
                    "training": {
                        "max_epochs": 100,
                        "learning_rate": 0.001,
                        "early_stopping": {"enable": True, "patience": 10},
                        "max_detection_per_image": {"enable": True, "max_detection_per_image": 100},
                    },
                    "evaluation": {},
                },
                Hyperparameters(
                    dataset_preparation=DatasetPreparationParameters(
                        augmentation=AugmentationParameters(
                            center_crop=CenterCrop(enable=True, ratio=0.8),
                            random_resize_crop=RandomResizeCrop(enable=True, ratio=0.5),
                            random_affine=RandomAffine(
                                enable=True, degrees=30, translate_x=0.1, translate_y=0.1, scale=0.9
                            ),
                            random_horizontal_flip=RandomHorizontalFlip(enable=True),
                            gaussian_blur=GaussianBlur(enable=True, kernel_size=3),
                            tiling=Tiling(enable=True, adaptive_tiling=True, tile_size=224, tile_overlap=32),
                        )
                    ),
                    training=TrainingHyperParameters(
                        max_epochs=100,
                        learning_rate=0.001,
                        early_stopping=EarlyStopping(enable=True, patience=10),
                        max_detection_per_image=MaxDetectionPerImage(enable=True, max_detection_per_image=100),
                    ),
                    evaluation=EvaluationParameters(),
                ),
            ),
            # Test case 3: Edge case values
            (
                {
                    "dataset_preparation": {
                        "augmentation": {
                            "center_crop": {"enable": True, "ratio": 0.1},
                            "random_horizontal_flip": {"enable": False},
                        }
                    },
                    "training": {
                        "max_epochs": 1,
                        "learning_rate": 0.0001,
                        "early_stopping": {"enable": True, "patience": 1},
                    },
                    "evaluation": {},
                },
                Hyperparameters(
                    dataset_preparation=DatasetPreparationParameters(
                        augmentation=AugmentationParameters(
                            center_crop=CenterCrop(enable=True, ratio=0.1),
                            random_horizontal_flip=RandomHorizontalFlip(enable=False),
                        )
                    ),
                    training=TrainingHyperParameters(
                        max_epochs=1, learning_rate=0.0001, early_stopping=EarlyStopping(enable=True, patience=1)
                    ),
                    evaluation=EvaluationParameters(),
                ),
            ),
        ],
    )
    def test_valid_hyperparameters(self, hyperparams_dict: dict, expected_params: Hyperparameters) -> None:
        # Create model from dict
        params = Hyperparameters(**hyperparams_dict)

        # Compare with expected model
        assert params == expected_params

        # Validate specific fields to ensure proper parsing
        assert (
            params.dataset_preparation.augmentation.random_horizontal_flip
            == expected_params.dataset_preparation.augmentation.random_horizontal_flip
        )

        assert params.training.early_stopping == expected_params.training.early_stopping
        assert params.training.max_epochs == expected_params.training.max_epochs
        assert params.training.learning_rate == expected_params.training.learning_rate

    def test_validation(self) -> None:
        """Test that validation errors in nested models are properly caught"""
        with pytest.raises(ValidationError):
            Hyperparameters(
                dataset_preparation=DatasetPreparationParameters(
                    augmentation=AugmentationParameters(random_horizontal_flip=RandomHorizontalFlip(enable=True))
                ),
                training=TrainingHyperParameters(
                    max_epochs=-10,  # Invalid value
                    learning_rate=0.01,
                ),
                evaluation=EvaluationParameters(),
            )

    def test_partial_hyperparameters(self):
        """Test that PartialHyperparameters works correctly with both partial and complete configurations."""
        # Test with a partial configuration
        partial_hyperparams = PartialHyperparameters.model_validate(
            {
                "training": {
                    "learning_rate": 0.005,
                    "early_stopping": {
                        "enable": True,
                    },
                }
            }
        )

        # Verify that specified fields are set correctly
        assert partial_hyperparams.training.learning_rate == 0.005
        assert partial_hyperparams.training.early_stopping.enable is True

        # Verify that unspecified fields are None
        assert partial_hyperparams.dataset_preparation is None
        assert partial_hyperparams.evaluation is None
        assert partial_hyperparams.training.max_epochs is None
        assert partial_hyperparams.training.early_stopping.patience is None

        # Test with a nested partial configuration
        nested_partial_hyperparams = PartialHyperparameters.model_validate(
            {"dataset_preparation": {"augmentation": {"center_crop": {"ratio": 0.75}}}}
        )

        # Verify that nested fields are set correctly
        assert nested_partial_hyperparams.dataset_preparation.augmentation.center_crop.ratio == 0.75
        assert nested_partial_hyperparams.dataset_preparation.augmentation.center_crop.enable is None

        # Test with a full configuration
        full_hyperparams = Hyperparameters(
            dataset_preparation=DatasetPreparationParameters(
                augmentation=AugmentationParameters(
                    center_crop=CenterCrop(enable=True, ratio=0.6),
                )
            ),
            training=TrainingHyperParameters(
                max_epochs=100,
                early_stopping=EarlyStopping(enable=True, patience=10),
                learning_rate=0.001,
            ),
            evaluation=EvaluationParameters(),
        )

        full_hyperparams_dict = full_hyperparams.model_dump()
        partial_hyperparams_full = PartialHyperparameters.model_validate(full_hyperparams_dict)

        # Verify that the full configuration converted to partial is identical to the original
        assert partial_hyperparams_full.model_dump() == full_hyperparams.model_dump()

        # Verify that validation still works for partial models
        with pytest.raises(ValidationError):
            PartialHyperparameters.model_validate(
                {
                    "training": {
                        "learning_rate": -0.1  # Invalid: must be > 0
                    }
                }
            )
