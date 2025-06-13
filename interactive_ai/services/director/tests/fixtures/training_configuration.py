# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
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
                dataset_size=256,  # This is a read-only parameter, not configurable by users
            ),
            filtering=Filtering(
                min_annotation_pixels=MinAnnotationPixels(enable=True, min_annotation_pixels=10),
                max_annotation_pixels=MaxAnnotationPixels(enable=True, max_annotation_pixels=1000),
                min_annotation_objects=MinAnnotationObjects(enable=True, min_annotation_objects=5),
                max_annotation_objects=MaxAnnotationObjects(enable=True, max_annotation_objects=100),
            ),
        )
    )


@pytest.fixture
def fxt_training_configuration_task_level(fxt_mongo_id, fxt_global_parameters, ftx_hyperparameters):
    yield TrainingConfiguration(
        id_=fxt_mongo_id(11),
        task_id=str(fxt_mongo_id(22)),
        global_parameters=fxt_global_parameters,
        hyperparameters=ftx_hyperparameters,
    )


@pytest.fixture
def fxt_training_configuration_task_level_rest_view(fxt_training_configuration_task_level):
    yield {
        "task_id": str(fxt_training_configuration_task_level.task_id),
        "dataset_preparation": {
            "augmentation": {
                "center_crop": [
                    {
                        "default_value": False,
                        "description": "Whether to apply center cropping to the image",
                        "key": "enable",
                        "name": "Enable center crop",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 1.0,
                        "description": "Ratio of original dimensions to keep when cropping",
                        "key": "ratio",
                        "max_value": None,
                        "min_value": 0.0,
                        "name": "Crop ratio",
                        "type": "float",
                        "value": 0.6,
                    },
                ]
            },
            "filtering": {
                "max_annotation_objects": [
                    {
                        "default_value": False,
                        "description": "Whether to apply maximum annotation objects filtering",
                        "key": "enable",
                        "name": "Enable maximum annotation objects filtering",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 10000,
                        "description": "Maximum number of objects in an annotation",
                        "key": "max_annotation_objects",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Maximum annotation objects",
                        "type": "int",
                        "value": 100,
                    },
                ],
                "max_annotation_pixels": [
                    {
                        "default_value": False,
                        "description": "Whether to apply maximum annotation pixels filtering",
                        "key": "enable",
                        "name": "Enable maximum annotation pixels filtering",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 10000,
                        "description": "Maximum number of pixels in an annotation",
                        "key": "max_annotation_pixels",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Maximum annotation pixels",
                        "type": "int",
                        "value": 1000,
                    },
                ],
                "min_annotation_pixels": [
                    {
                        "default_value": False,
                        "description": "Whether to apply minimum annotation pixels filtering",
                        "key": "enable",
                        "name": "Enable minimum annotation pixels filtering",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 1,
                        "description": "Minimum number of pixels in an annotation",
                        "key": "min_annotation_pixels",
                        "max_value": 200000000,
                        "min_value": 0,
                        "name": "Minimum annotation pixels",
                        "type": "int",
                        "value": 10,
                    },
                ],
                "min_annotation_objects": [
                    {
                        "default_value": False,
                        "description": "Whether to apply minimum annotation objects filtering",
                        "key": "enable",
                        "name": "Enable minimum annotation objects filtering",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 1,
                        "description": "Minimum number of objects in an annotation",
                        "key": "min_annotation_objects",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Minimum annotation objects",
                        "type": "int",
                        "value": 5,
                    },
                ],
            },
            "subset_split": [
                {
                    "default_value": 70,
                    "description": "Percentage of data to use for training",
                    "key": "training",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Training percentage",
                    "type": "int",
                    "value": 70,
                },
                {
                    "default_value": 20,
                    "description": "Percentage of data to use for validation",
                    "key": "validation",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Validation percentage",
                    "type": "int",
                    "value": 20,
                },
                {
                    "default_value": 10,
                    "description": "Percentage of data to use for testing",
                    "key": "test",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Test percentage",
                    "type": "int",
                    "value": 10,
                },
                {
                    "default_value": True,
                    "description": "Whether to automatically select data for each subset",
                    "key": "auto_selection",
                    "name": "Auto selection",
                    "type": "bool",
                    "value": True,
                },
                {
                    "default_value": False,
                    "description": "Whether to remix data between subsets",
                    "key": "remixing",
                    "name": "Remixing",
                    "type": "bool",
                    "value": False,
                },
                {
                    "default_value": None,
                    "description": "Total size of the dataset (read-only parameter, not configurable by users)",
                    "key": "dataset_size",
                    "max_value": None,
                    "min_value": 0,
                    "name": "Dataset size",
                    "type": "int",
                    "value": 256,
                },
            ],
        },
        "training": [
            {
                "default_value": 1000,
                "description": "Maximum number of training epochs to run",
                "key": "max_epochs",
                "max_value": None,
                "min_value": 0,
                "name": "Maximum epochs",
                "type": "int",
                "value": 100,
            },
            {
                "default_value": 0.001,
                "description": "Base learning rate for the optimizer",
                "key": "learning_rate",
                "max_value": 1.0,
                "min_value": 0.0,
                "name": "Learning rate",
                "type": "float",
                "value": 0.001,
            },
            {
                "early_stopping": [
                    {
                        "default_value": False,
                        "description": "Whether to stop training early when performance stops improving",
                        "key": "enable",
                        "name": "Enable early stopping",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 1,
                        "description": "Number of epochs with no improvement after which training will be stopped",
                        "key": "patience",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Patience",
                        "type": "int",
                        "value": 10,
                    },
                ],
                "max_detection_per_image": [
                    {
                        "default_value": False,
                        "description": "Whether to limit the number of detections per image",
                        "key": "enable",
                        "name": "Enable maximum detection per image",
                        "type": "bool",
                        "value": False,
                    },
                    {
                        "default_value": 10000,
                        "description": "Maximum number of objects that can be detected in a single image, "
                        "only applicable for instance segmentation models",
                        "key": "max_detection_per_image",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Maximum number of detections per image",
                        "type": "int",
                        "value": 10000,
                    },
                ],
            },
        ],
        "evaluation": [],
    }


@pytest.fixture
def fxt_partial_training_configuration_manifest_level(fxt_mongo_id):
    # Manifest level configuration contains parameters related to a model architecture
    # if there is a conflict with task level configuration, manifest level configuration takes precedence
    partial_config_dict = {
        "id_": fxt_mongo_id(12),
        "task_id": fxt_mongo_id(22),
        "model_manifest_id": "test_model_manifest_id",
        "global_parameters": {
            "dataset_preparation": {
                "subset_split": {
                    "training": 80,
                    "validation": 10,
                    "test": 10,
                    "dataset_size": 256,  # Note: this is a read-only parameter, not configurable by users
                }
            }
        },
        "hyperparameters": {
            "dataset_preparation": {
                "augmentation": {
                    "random_affine": {
                        "enable": True,
                        "degrees": 15,
                    },
                    "tiling": {
                        "enable": True,
                        "adaptive_tiling": False,
                        "tile_size": 256,
                        "tile_overlap": 64,
                    },
                },
            },
            "training": {
                "max_epochs": 50,
                "learning_rate": 0.05,
            },
        },
    }
    yield PartialTrainingConfiguration.model_validate(partial_config_dict)


@pytest.fixture
def fxt_training_configuration_full_rest_view(
    fxt_training_configuration_task_level_rest_view, fxt_partial_training_configuration_manifest_level
):
    # Full configuration combines task level and manifest level configurations
    yield {
        "task_id": str(fxt_partial_training_configuration_manifest_level.task_id),
        "model_manifest_id": fxt_partial_training_configuration_manifest_level.model_manifest_id,
        "dataset_preparation": {
            "augmentation": {
                "center_crop": [
                    {
                        "default_value": False,
                        "description": "Whether to apply center cropping to the image",
                        "key": "enable",
                        "name": "Enable center crop",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 1.0,
                        "description": "Ratio of original dimensions to keep when cropping",
                        "key": "ratio",
                        "max_value": None,
                        "min_value": 0.0,
                        "name": "Crop ratio",
                        "type": "float",
                        "value": 0.6,
                    },
                ],
                "random_affine": [
                    {
                        "default_value": False,
                        "description": "Whether to apply random affine transformations to the image",
                        "key": "enable",
                        "name": "Enable random affine",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 0.0,
                        "description": "Maximum rotation angle in degrees",
                        "key": "degrees",
                        "max_value": None,
                        "min_value": 0.0,
                        "name": "Rotation degrees",
                        "type": "float",
                        "value": 15.0,
                    },
                    {
                        "default_value": 0.0,
                        "description": "Maximum horizontal translation as a fraction of image width",
                        "key": "translate_x",
                        "max_value": None,
                        "min_value": None,
                        "name": "Horizontal translation",
                        "type": "float",
                        "value": 0.0,
                    },
                    {
                        "default_value": 0.0,
                        "description": "Maximum vertical translation as a fraction of image height",
                        "key": "translate_y",
                        "max_value": None,
                        "min_value": None,
                        "name": "Vertical translation",
                        "type": "float",
                        "value": 0.0,
                    },
                    {
                        "default_value": 1.0,
                        "description": "Scaling factor for the image during affine transformation",
                        "key": "scale",
                        "max_value": None,
                        "min_value": None,
                        "name": "Scale factor",
                        "type": "float",
                        "value": 1.0,
                    },
                ],
                "tiling": [
                    {
                        "default_value": False,
                        "description": "Whether to apply tiling to the image",
                        "key": "enable",
                        "name": "Enable tiling",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": False,
                        "description": "Whether to use adaptive tiling based on image content",
                        "key": "adaptive_tiling",
                        "name": "Adaptive tiling",
                        "type": "bool",
                        "value": False,
                    },
                    {
                        "default_value": 128,
                        "description": "Size of each tile in pixels",
                        "key": "tile_size",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Tile size",
                        "type": "int",
                        "value": 256,
                    },
                    {
                        "default_value": 64,
                        "description": "Overlap between adjacent tiles in pixels",
                        "key": "tile_overlap",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Tile overlap",
                        "type": "int",
                        "value": 64,
                    },
                ],
            },
            "filtering": {
                "max_annotation_objects": [
                    {
                        "default_value": False,
                        "description": "Whether to apply maximum annotation objects filtering",
                        "key": "enable",
                        "name": "Enable maximum annotation objects filtering",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 10000,
                        "description": "Maximum number of objects in an annotation",
                        "key": "max_annotation_objects",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Maximum annotation objects",
                        "type": "int",
                        "value": 100,
                    },
                ],
                "max_annotation_pixels": [
                    {
                        "default_value": False,
                        "description": "Whether to apply maximum annotation pixels filtering",
                        "key": "enable",
                        "name": "Enable maximum annotation pixels filtering",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 10000,
                        "description": "Maximum number of pixels in an annotation",
                        "key": "max_annotation_pixels",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Maximum annotation pixels",
                        "type": "int",
                        "value": 1000,
                    },
                ],
                "min_annotation_pixels": [
                    {
                        "default_value": False,
                        "description": "Whether to apply minimum annotation pixels filtering",
                        "key": "enable",
                        "name": "Enable minimum annotation pixels filtering",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 1,
                        "description": "Minimum number of pixels in an annotation",
                        "key": "min_annotation_pixels",
                        "max_value": 200000000,
                        "min_value": 0,
                        "name": "Minimum annotation pixels",
                        "type": "int",
                        "value": 10,
                    },
                ],
                "min_annotation_objects": [
                    {
                        "default_value": False,
                        "description": "Whether to apply minimum annotation objects filtering",
                        "key": "enable",
                        "name": "Enable minimum annotation objects filtering",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 1,
                        "description": "Minimum number of objects in an annotation",
                        "key": "min_annotation_objects",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Minimum annotation objects",
                        "type": "int",
                        "value": 5,
                    },
                ],
            },
            "subset_split": [
                {
                    "default_value": 70,
                    "description": "Percentage of data to use for training",
                    "key": "training",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Training percentage",
                    "type": "int",
                    "value": 80,
                },
                {
                    "default_value": 20,
                    "description": "Percentage of data to use for validation",
                    "key": "validation",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Validation percentage",
                    "type": "int",
                    "value": 10,
                },
                {
                    "default_value": 10,
                    "description": "Percentage of data to use for testing",
                    "key": "test",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Test percentage",
                    "type": "int",
                    "value": 10,
                },
                {
                    "default_value": True,
                    "description": "Whether to automatically select data for each subset",
                    "key": "auto_selection",
                    "name": "Auto selection",
                    "type": "bool",
                    "value": True,
                },
                {
                    "default_value": False,
                    "description": "Whether to remix data between subsets",
                    "key": "remixing",
                    "name": "Remixing",
                    "type": "bool",
                    "value": False,
                },
                {
                    "default_value": None,
                    "description": "Total size of the dataset (read-only parameter, not configurable by users)",
                    "key": "dataset_size",
                    "max_value": None,
                    "min_value": 0,
                    "name": "Dataset size",
                    "type": "int",
                    "value": 256,
                },
            ],
        },
        "training": [
            {
                "default_value": 1000,
                "description": "Maximum number of training epochs to run",
                "key": "max_epochs",
                "max_value": None,
                "min_value": 0,
                "name": "Maximum epochs",
                "type": "int",
                "value": 50,
            },
            {
                "default_value": 0.001,
                "description": "Base learning rate for the optimizer",
                "key": "learning_rate",
                "max_value": 1.0,
                "min_value": 0.0,
                "name": "Learning rate",
                "type": "float",
                "value": 0.05,
            },
            {
                "early_stopping": [
                    {
                        "default_value": False,
                        "description": "Whether to stop training early when performance stops improving",
                        "key": "enable",
                        "name": "Enable early stopping",
                        "type": "bool",
                        "value": True,
                    },
                    {
                        "default_value": 1,
                        "description": "Number of epochs with no improvement after which training will be stopped",
                        "key": "patience",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Patience",
                        "type": "int",
                        "value": 10,
                    },
                ],
                "max_detection_per_image": [
                    {
                        "default_value": False,
                        "description": "Whether to limit the number of detections per image",
                        "key": "enable",
                        "name": "Enable maximum detection per image",
                        "type": "bool",
                        "value": False,
                    },
                    {
                        "default_value": 10000,
                        "description": "Maximum number of objects that can be detected in a single image, "
                        "only applicable for instance segmentation models",
                        "key": "max_detection_per_image",
                        "max_value": None,
                        "min_value": 0,
                        "name": "Maximum number of detections per image",
                        "type": "int",
                        "value": 10000,
                    },
                ],
            },
        ],
        "evaluation": [],
    }
