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
    RandomAffine,
    Tiling,
    TrainingHyperParameters,
)
from geti_configuration_tools.training_configuration import (
    Filtering,
    GlobalDatasetPreparationParameters,
    GlobalParameters,
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
            min_annotation_pixels=10,
            early_stopping=EarlyStopping(enable=True, patience=5),
        ),
        evaluation=EvaluationParameters(),
    )


@pytest.fixture
def ftx_hyperparameters_2():
    yield Hyperparameters(
        dataset_preparation=DatasetPreparationParameters(
            augmentation=AugmentationParameters(
                random_affine=RandomAffine(enable=True, degrees=0.2),
                tiling=Tiling(
                    enable=True,
                    adaptive_tiling=False,
                    tile_size=512,
                    tile_overlap=64,
                ),
            )
        ),
        training=TrainingHyperParameters(
            max_epochs=10,
            max_detection_per_image=5,
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
            ),
        )
    )


@pytest.fixture
def fxt_global_parameters_2():
    yield GlobalParameters(
        dataset_preparation=GlobalDatasetPreparationParameters(
            subset_split=SubsetSplit(
                training=50,
                validation=30,
                test=20,
                auto_selection=False,
                remixing=False,
            ),
            filtering=Filtering(
                min_annotation_pixels=10,
                max_annotation_pixels=100,
                max_annotation_objects=1000,
            ),
        )
    )


@pytest.fixture
def fxt_training_configuration_task_level(fxt_mongo_id, fxt_global_parameters, ftx_hyperparameters):
    yield TrainingConfiguration(
        id_=fxt_mongo_id(11),
        task_id=fxt_mongo_id(22),
        global_parameters=fxt_global_parameters,
        hyperparameters=ftx_hyperparameters,
    )


@pytest.fixture
def fxt_training_configuration_task_level_rest_view(fxt_training_configuration_task_level):
    yield {
        "task_id": str(fxt_training_configuration_task_level.model_extra["task_id"]),
        "dataset_preparation": {
            "subset_split": [
                {
                    "key": "training",
                    "name": "Training percentage",
                    "description": "Percentage of data to use for training",
                    "value": 70,
                    "default_value": 70,
                    "type": "int",
                    "min_value": 1,
                    "max_value": None,
                },
                {
                    "key": "validation",
                    "name": "Validation percentage",
                    "description": "Percentage of data to use for validation",
                    "value": 20,
                    "default_value": 20,
                    "type": "int",
                    "min_value": 1,
                    "max_value": None,
                },
                {
                    "key": "test",
                    "name": "Test percentage",
                    "description": "Percentage of data to use for testing",
                    "value": 10,
                    "default_value": 10,
                    "type": "int",
                    "min_value": 1,
                    "max_value": None,
                },
                {
                    "key": "auto_selection",
                    "name": "Auto selection",
                    "description": "Whether to automatically select data for each subset",
                    "value": True,
                    "default_value": True,
                    "type": "bool",
                },
                {
                    "key": "remixing",
                    "name": "Remixing",
                    "description": "Whether to remix data between subsets",
                    "value": False,
                    "default_value": False,
                    "type": "bool",
                },
            ],
            "filtering": [
                {
                    "key": "min_annotation_pixels",
                    "name": "Minimum annotation pixels",
                    "description": "Minimum number of pixels in an annotation",
                    "value": 10,
                    "default_value": 1,
                    "type": "int",
                    "min_value": 0,
                    "max_value": None,
                },
            ],
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
                        "key": "ratio",
                        "name": "Crop ratio",
                        "description": "Ratio of original dimensions to keep when cropping",
                        "value": 0.6,
                        "default_value": 1.0,
                        "type": "float",
                        "min_value": 0.0,
                        "max_value": None,
                    },
                ]
            },
        },
        "training": [
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
                        "value": 5,
                    },
                ]
            },
        ],
        "evaluation": [],
    }


@pytest.fixture
def fxt_training_configuration_manifest_level(fxt_mongo_id, fxt_global_parameters_2, ftx_hyperparameters_2):
    # Manifest level configuration contains parameters related to a model architecture
    # if there is a conflict with task level configuration, manifest level configuration takes precedence
    yield TrainingConfiguration(
        id_=fxt_mongo_id(12),
        task_id=fxt_mongo_id(22),
        model_manifest_id="test_model_manifest_id",
        global_parameters=fxt_global_parameters_2,
        hyperparameters=ftx_hyperparameters_2,
    )


@pytest.fixture
def fxt_training_configuration_full_rest_view(fxt_training_configuration_manifest_level):
    # REST view for fxt_training_configuration_task_level and fxt_training_configuration_manifest_level
    yield {
        "task_id": str(fxt_training_configuration_manifest_level.model_extra["task_id"]),
        "model_manifest_id": fxt_training_configuration_manifest_level.model_manifest_id,
        "dataset_preparation": {
            "subset_split": [
                {
                    "key": "training",
                    "name": "Training percentage",
                    "description": "Percentage of data to use for training",
                    "value": 50,
                    "default_value": 70,
                    "type": "int",
                    "min_value": 1,
                    "max_value": None,
                },
                {
                    "key": "validation",
                    "name": "Validation percentage",
                    "description": "Percentage of data to use for validation",
                    "value": 30,
                    "default_value": 20,
                    "type": "int",
                    "min_value": 1,
                    "max_value": None,
                },
                {
                    "key": "test",
                    "name": "Test percentage",
                    "description": "Percentage of data to use for testing",
                    "value": 20,
                    "default_value": 10,
                    "type": "int",
                    "min_value": 1,
                    "max_value": None,
                },
                {
                    "key": "auto_selection",
                    "name": "Auto selection",
                    "description": "Whether to automatically select data for each subset",
                    "value": False,
                    "default_value": True,
                    "type": "bool",
                },
                {
                    "key": "remixing",
                    "name": "Remixing",
                    "description": "Whether to remix data between subsets",
                    "value": False,
                    "default_value": False,
                    "type": "bool",
                },
            ],
            "filtering": [
                {
                    "key": "min_annotation_pixels",
                    "name": "Minimum annotation pixels",
                    "description": "Minimum number of pixels in an annotation",
                    "value": 10,
                    "default_value": 1,
                    "type": "int",
                    "min_value": 0,
                    "max_value": None,
                },
                {
                    "key": "max_annotation_pixels",
                    "name": "Maximum annotation pixels",
                    "description": "Maximum number of pixels in an annotation",
                    "value": 100,
                    "default_value": None,
                    "type": "int",
                    "min_value": 1,
                    "max_value": None,
                },
                {
                    "key": "max_annotation_objects",
                    "name": "Maximum annotation objects",
                    "description": "Maximum number of objects in an annotation",
                    "value": 1000,
                    "default_value": None,
                    "type": "int",
                    "min_value": 1,
                    "max_value": None,
                },
            ],
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
                        "key": "ratio",
                        "name": "Crop ratio",
                        "description": "Ratio of original dimensions to keep when cropping",
                        "value": 0.6,
                        "default_value": 1.0,
                        "type": "float",
                        "min_value": 0.0,
                        "max_value": None,
                    },
                ],
                "random_affine": [
                    {
                        "key": "enable",
                        "name": "Enable random affine",
                        "description": "Whether to apply random affine transformations to the image",
                        "value": True,
                        "default_value": False,
                        "type": "bool",
                    },
                    {
                        "key": "degrees",
                        "name": "Rotation degrees",
                        "description": "Maximum rotation angle in degrees",
                        "value": 0.2,
                        "default_value": 0.0,
                        "type": "float",
                        "min_value": None,
                        "max_value": None,
                    },
                ],
                "tiling": [
                    {
                        "key": "enable",
                        "name": "Enable tiling",
                        "description": "Whether to apply tiling to the image",
                        "value": True,
                        "default_value": False,
                        "type": "bool",
                    },
                    {
                        "key": "adaptive_tiling",
                        "name": "Adaptive tiling",
                        "description": "Whether to use adaptive tiling based on image content",
                        "value": False,
                        "default_value": False,
                        "type": "bool",
                    },
                    {
                        "key": "tile_size",
                        "name": "Tile size",
                        "description": "Size of each tile in pixels",
                        "value": 512,
                        "default_value": 128,
                        "type": "int",
                        "min_value": 0,
                        "max_value": None,
                    },
                    {
                        "key": "tile_overlap",
                        "name": "Tile overlap",
                        "description": "Overlap between adjacent tiles in pixels",
                        "value": 64,
                        "default_value": 64,
                        "type": "int",
                        "min_value": 0,
                        "max_value": None,
                    },
                ],
            },
        },
        "training": [
            {
                "key": "max_epochs",
                "name": "Maximum epochs",
                "description": "Maximum number of training epochs to run",
                "value": 10,
                "default_value": None,
                "type": "int",
                "min_value": 0,
                "max_value": None,
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
                "key": "max_detection_per_image",
                "name": "Maximum number of detections per image",
                "description": (
                    "Maximum number of objects that can be detected in a single image, "
                    "only applicable for instance segmentation models"
                ),
                "value": 5,
                "default_value": None,
                "type": "int",
                "min_value": 0,
                "max_value": None,
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
                        "value": 5,
                    },
                ]
            },
        ],
        "evaluation": [],
    }
