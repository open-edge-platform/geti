# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any

from geti_types import ID, PersistentEntity
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .hyperparameters import Hyperparameters
from .utils import partial_model


class SubsetSplit(BaseModel):
    """
    Parameters for splitting a dataset into training, validation, and test subsets.
    The sum of training, validation, and test percentages must equal 100.
    """

    training: int = Field(
        ge=1, le=100, default=70, title="Training percentage", description="Percentage of data to use for training"
    )
    validation: int = Field(
        ge=1, le=100, default=20, title="Validation percentage", description="Percentage of data to use for validation"
    )
    test: int = Field(
        ge=1, le=100, default=10, title="Test percentage", description="Percentage of data to use for testing"
    )
    auto_selection: bool = Field(
        default=True, title="Auto selection", description="Whether to automatically select data for each subset"
    )
    remixing: bool = Field(default=False, title="Remixing", description="Whether to remix data between subsets")
    dataset_size: int | None = Field(
        ge=0,
        default=None,
        title="Dataset size",
        description="Total size of the dataset (read-only parameter, not configurable by users)",
        exclude=True,  # exclude read-only parameter from serialization
        json_schema_extra={"default_value": None},
    )

    @model_validator(mode="after")
    def validate_subsets(self) -> "SubsetSplit":
        if (self.training + self.validation + self.test) != 100:
            raise ValueError("Sum of subsets should be equal to 100")
        return self


class MinAnnotationPixels(BaseModel):
    """Parameters for minimum annotation pixels."""

    enable: bool = Field(
        default=False,
        title="Enable minimum annotation pixels filtering",
        description="Whether to apply minimum annotation pixels filtering",
    )
    min_annotation_pixels: int = Field(
        gt=0,
        le=200000000,  # reasonable upper limit for pixel count to 200MP
        default=1,
        title="Minimum annotation pixels",
        description="Minimum number of pixels in an annotation",
    )


class MaxAnnotationPixels(BaseModel):
    """Parameters for maximum annotation pixels."""

    enable: bool = Field(
        default=False,
        title="Enable maximum annotation pixels filtering",
        description="Whether to apply maximum annotation pixels filtering",
    )
    max_annotation_pixels: int = Field(
        gt=0, default=10000, title="Maximum annotation pixels", description="Maximum number of pixels in an annotation"
    )


class MinAnnotationObjects(BaseModel):
    """Parameters for maximum annotation objects."""

    enable: bool = Field(
        default=False,
        title="Enable minimum annotation objects filtering",
        description="Whether to apply minimum annotation objects filtering",
    )
    min_annotation_objects: int = Field(
        gt=0,
        default=1,
        title="Minimum annotation objects",
        description="Minimum number of objects in an annotation",
    )


class MaxAnnotationObjects(BaseModel):
    """Parameters for maximum annotation objects."""

    enable: bool = Field(
        default=False,
        title="Enable maximum annotation objects filtering",
        description="Whether to apply maximum annotation objects filtering",
    )
    max_annotation_objects: int = Field(
        gt=0,
        default=10000,
        title="Maximum annotation objects",
        description="Maximum number of objects in an annotation",
    )


class Filtering(BaseModel):
    """Parameters for filtering annotations in the dataset."""

    min_annotation_pixels: MinAnnotationPixels = Field(
        title="Minimum annotation pixels", description="Minimum number of pixels in an annotation"
    )
    max_annotation_pixels: MaxAnnotationPixels = Field(
        title="Maximum annotation pixels", description="Maximum number of pixels in an annotation"
    )
    min_annotation_objects: MinAnnotationObjects = Field(
        title="Minimum annotation objects", description="Minimum number of objects in an annotation"
    )
    max_annotation_objects: MaxAnnotationObjects = Field(
        title="Maximum annotation objects", description="Maximum number of objects in an annotation"
    )


class GlobalDatasetPreparationParameters(BaseModel):
    """
    Parameters for preparing a dataset for training within the global configuration.
    Controls data splitting and filtering before being passed for the training.
    """

    subset_split: SubsetSplit = Field(title="Subset split", description="Configuration for splitting data into subsets")
    filtering: Filtering = Field(title="Filtering", description="Configuration for filtering annotations")


class GlobalParameters(BaseModel):
    """
    Global parameters that are used within the application but are not directly passed to the training backend.
    These parameters still impact the final training outcome by controlling dataset preparation.
    """

    dataset_preparation: GlobalDatasetPreparationParameters = Field(
        title="Dataset preparation", description="Parameters for preparing the dataset"
    )


class TrainingConfiguration(BaseModel, PersistentEntity):
    """Configuration for model training"""

    def __init__(self, id_: ID, ephemeral: bool = True, **data):
        # first initialize the Pydantic BaseModel with all arguments
        BaseModel.__init__(self, **data)

        # then initialize PersistentEntity with id and ephemeral parameters
        PersistentEntity.__init__(self, id_=id_, ephemeral=ephemeral)

    task_id: str = Field(title="Task ID", description="Unique identifier for the task")
    model_config = ConfigDict(protected_namespaces=())  # avoid conflict with "model_" namespace
    model_manifest_id: str | None = Field(
        default=None,
        title="Model manifest ID",
        description="ID for the model manifest that defines the supported parameters and capabilities for training",
    )
    global_parameters: GlobalParameters = Field(
        title="Global parameters", description="Global configuration parameters for training"
    )
    hyperparameters: Hyperparameters = Field(title="Hyperparameters", description="Hyperparameters for training")

    def __eq__(self, other: object) -> bool:
        """
        Compares two ProjectConfiguration instances.

        Checks if both objects have the same ID and task configurations.
        """
        if not isinstance(other, TrainingConfiguration):
            return False

        # Compare IDs
        if self.id_ != other.id_ or self.model_manifest_id != other.model_manifest_id:
            return False

        # Compare parameters
        return self.global_parameters == other.global_parameters and self.hyperparameters == other.hyperparameters


@partial_model
class NullTrainingConfiguration(TrainingConfiguration):
    """
    Null object implementation for TrainingConfiguration.

    This class implements the Null Object Pattern to represent a "non-existent" training configuration.
    """

    def __init__(self) -> None:
        TrainingConfiguration.__init__(
            self,
            id_=ID(),
            task_id=ID(),
            ephemeral=True,
        )

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:  # noqa: ARG002
        return {}


@partial_model
class PartialTrainingConfiguration(TrainingConfiguration):
    """
    A partial version of `TrainingConfiguration` with all fields optional.

    Enables flexible updates and partial validation, making it suitable for scenarios
    where only a subset of the configuration needs to be specified or changed.
    """

    def __init__(self, id_: ID = ID(), ephemeral: bool = True, **data):
        super().__init__(id_, ephemeral, **data)

    @model_validator(mode="after")
    def validate_identifiers(self) -> "PartialTrainingConfiguration":
        if not self.task_id:
            raise ValueError("task_id must be provided in the configuration.")
        return self


@partial_model
class PartialGlobalParameters(GlobalParameters):
    """
    A partial version of `GlobalParameters` with all fields optional.

    Enables flexible updates and partial validation, making it suitable for scenarios
    where only a subset of the configuration needs to be specified or changed.
    """
