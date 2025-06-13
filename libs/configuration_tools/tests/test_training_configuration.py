# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID
from pydantic import ValidationError

from geti_configuration_tools.hyperparameters import (
    AugmentationParameters,
    CenterCrop,
    DatasetPreparationParameters,
    EarlyStopping,
    EvaluationParameters,
    Hyperparameters,
    TrainingHyperParameters,
)
from geti_configuration_tools.training_configuration import (
    Filtering,
    GlobalDatasetPreparationParameters,
    GlobalParameters,
    MaxAnnotationObjects,
    MaxAnnotationPixels,
    MinAnnotationObjects,
    MinAnnotationPixels,
    NullTrainingConfiguration,
    PartialGlobalParameters,
    PartialTrainingConfiguration,
    SubsetSplit,
    TrainingConfiguration,
)


@pytest.fixture
def ftx_hyperparameters():
    yield Hyperparameters(
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
                min_annotation_pixels=MinAnnotationPixels(enable=True, min_annotation_pixels=10),
                max_annotation_pixels=MaxAnnotationPixels(enable=True, max_annotation_pixels=1000),
                min_annotation_objects=MinAnnotationObjects(enable=True, min_annotation_objects=5),
                max_annotation_objects=MaxAnnotationObjects(enable=True, max_annotation_objects=100),
            ),
        )
    )


class TestTrainingConfiguration:
    def test_valid_training_configuration(self, fxt_global_parameters, ftx_hyperparameters) -> None:
        # Create a valid TrainingConfiguration
        training_config = TrainingConfiguration(
            id_=ID("test_training_config"),
            task_id=ID("test_task"),
            global_parameters=fxt_global_parameters,
            hyperparameters=ftx_hyperparameters,
        )

        # Verify the created config properties
        assert training_config.global_parameters.dataset_preparation.subset_split.training == 70
        assert training_config.global_parameters.dataset_preparation.subset_split.validation == 20
        assert training_config.global_parameters.dataset_preparation.subset_split.test == 10
        assert training_config.hyperparameters.training.max_epochs == 100
        assert training_config.hyperparameters.training.early_stopping.enable
        assert training_config.hyperparameters.training.early_stopping.patience == 10

    def test_invalid_subset_split(self, ftx_hyperparameters) -> None:
        # Test that validation fails when subset percentages don't add up to 100
        with pytest.raises(ValidationError) as excinfo:
            TrainingConfiguration(
                id_=ID("test_training_config"),
                task_id=ID("test_task"),
                global_parameters=GlobalParameters(
                    dataset_preparation=GlobalDatasetPreparationParameters(
                        subset_split=SubsetSplit(
                            training=60,  # Sum is 90, not 100
                            validation=20,
                            test=10,
                            auto_selection=True,
                            remixing=False,
                        ),
                        filtering=Filtering(
                            min_annotation_pixels=MinAnnotationPixels(),
                            max_annotation_pixels=MaxAnnotationPixels(),
                            min_annotation_objects=MinAnnotationObjects(),
                            max_annotation_objects=MaxAnnotationObjects(),
                        ),
                    )
                ),
                hyperparameters=ftx_hyperparameters,
            )

        assert "Sum of subsets should be equal to 100" in str(excinfo.value)

    def test_invalid_annotation_pixels(self, ftx_hyperparameters) -> None:
        # Test validation for annotation pixels
        with pytest.raises(ValidationError):
            TrainingConfiguration(
                id_=ID("test_training_config"),
                task_id=ID("test_task"),
                global_parameters=GlobalParameters(
                    dataset_preparation=GlobalDatasetPreparationParameters(
                        subset_split=SubsetSplit(),
                        filtering=Filtering(
                            min_annotation_pixels=MinAnnotationPixels(
                                enable=True,
                                min_annotation_pixels=0,  # Invalid: must be > 0
                            ),
                            max_annotation_pixels=MaxAnnotationPixels(),
                            min_annotation_objects=MinAnnotationObjects(),
                            max_annotation_objects=MaxAnnotationObjects(),
                        ),
                    )
                ),
                hyperparameters=ftx_hyperparameters,
            )

    def test_null_training_configuration(self) -> None:
        null_training_config = NullTrainingConfiguration()
        assert null_training_config.model_dump() == {}

    def test_partial_training_configuration(self, fxt_global_parameters, ftx_hyperparameters) -> None:
        """Test that PartialTrainingConfiguration works correctly with both partial and complete configurations."""
        partial_training_config_incomplete = PartialTrainingConfiguration.model_validate(
            {
                "id_": ID("partial_config"),
                "task_id": ID("test_task"),
                "model_manifest_id": "test_manifest",
                "global_parameters": {
                    "dataset_preparation": {
                        "filtering": {
                            "min_annotation_pixels": {
                                "min_annotation_pixels": 42,
                            },
                        }
                    }
                },
            }
        )
        global_parameters = partial_training_config_incomplete.global_parameters
        assert partial_training_config_incomplete.model_manifest_id == "test_manifest"
        assert partial_training_config_incomplete.id_ == ID("partial_config")
        assert partial_training_config_incomplete.task_id == ID("test_task")
        assert global_parameters.dataset_preparation.filtering.min_annotation_pixels.min_annotation_pixels == 42
        assert global_parameters.dataset_preparation.filtering.min_annotation_pixels.enable is None
        assert global_parameters.dataset_preparation.subset_split is None

        # Full configuration
        training_config = TrainingConfiguration(
            id_=ID("test_training_config"),
            task_id=ID("test_task"),
            global_parameters=fxt_global_parameters,
            hyperparameters=ftx_hyperparameters,
        )
        full_training_config_dict = training_config.model_dump()
        full_training_config_dict["id_"] = ID("full_config")
        partial_training_config_full = PartialTrainingConfiguration.model_validate(full_training_config_dict)

        assert partial_training_config_full.model_dump() == training_config.model_dump()

    def test_partial_global_parameters(self, fxt_global_parameters) -> None:
        """Test that PartialGlobalParameters works correctly with both partial and complete configurations."""
        # Test with a partial configuration
        partial_global_params = PartialGlobalParameters.model_validate(
            {
                "dataset_preparation": {
                    "subset_split": {
                        "training": 42,
                        "validation": 48,
                        "test": 10,
                    }
                }
            }
        )

        # Verify that specified fields are set correctly
        assert partial_global_params.dataset_preparation.subset_split.training == 42
        assert partial_global_params.dataset_preparation.subset_split.validation == 48
        assert partial_global_params.dataset_preparation.subset_split.test == 10

        # Verify that subset validator still works e.g. sum must be 100
        with pytest.raises(ValidationError):
            PartialGlobalParameters.model_validate(
                {
                    "dataset_preparation": {
                        "subset_split": {
                            "training": 1,
                            "validation": 1,
                            "test": 1,
                        }
                    }
                }
            )

        # Verify that unspecified fields are None
        assert partial_global_params.dataset_preparation.subset_split
        assert partial_global_params.dataset_preparation.filtering is None

        # Test with a full configuration
        full_global_params_dict = fxt_global_parameters.model_dump()
        partial_global_params_full = PartialGlobalParameters.model_validate(full_global_params_dict)

        assert partial_global_params_full.model_dump() == fxt_global_parameters.model_dump()
