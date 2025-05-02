# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This file defines the ModelConfiguration, Model and Model classes"""

import datetime
import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import TYPE_CHECKING, Optional

from iai_core_py.adapters.adapter import IAdapter, ReferenceAdapter
from iai_core_py.adapters.model_adapter import DataSource, ExportableCodeAdapter, ModelAdapter
from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.configuration.elements.hyper_parameters import NullHyperParameters
from iai_core_py.entities.label_schema import LabelSchema, NullLabelSchema
from iai_core_py.entities.metrics import NullPerformance, Performance
from iai_core_py.entities.model_storage import ModelStorage, ModelStorageIdentifier, NullModelStorage
from iai_core_py.entities.model_template import TargetDevice
from iai_core_py.entities.persistent_entity import PersistentEntity
from iai_core_py.utils.time_utils import now

from geti_types import ID

if TYPE_CHECKING:
    from iai_core_py.entities.datasets import Dataset
    from iai_core_py.entities.project import Project


class ModelConfiguration:
    """
    This class represents the task configuration which was used to generate a specific model.

    Those are the parameters that a task may need in order to use the model.

    :param configurable_parameters: Task configurable parameters used to generate the model
    :param label_schema: Label schema inside the project used to generate the model
    """

    configurable_parameters: ConfigurableParameters

    def __init__(
        self,
        configurable_parameters: ConfigurableParameters,
        label_schema: LabelSchema,
    ) -> None:
        self.configurable_parameters = configurable_parameters
        self.__label_schema = label_schema
        self.__label_schema_adapter: IAdapter[LabelSchema] = ReferenceAdapter(label_schema)

    @classmethod
    def with_adapters(
        cls,
        configurable_parameters: ConfigurableParameters,
        label_schema_adapter: IAdapter[LabelSchema],
    ):
        """Instantiate the ModelConfiguration with an adapter for the LabelSchema"""
        inst = cls(
            configurable_parameters=configurable_parameters,
            label_schema=NullLabelSchema(),
        )
        inst.__label_schema_adapter = label_schema_adapter
        return inst

    def get_label_schema(self) -> LabelSchema:
        """Get the LabelSchema"""
        return self.__label_schema_adapter.get()

    @property
    def label_schema_id(self) -> ID:
        """Get the ID of the label schema"""
        return self.__label_schema_adapter.id_


class ModelStatus(IntEnum):
    """Indicates the status of the last training result"""

    NOT_READY = auto()  # Model is not ready to be trained
    TRAINED_NO_STATS = auto()  # Model is trained but not evaluated yet
    SUCCESS = auto()  # Model trained successfully and improved
    FAILED = auto()  # Model failed during training, e.g. an error occurred or user cancelled training
    NOT_IMPROVED = auto()  # Model trained successfully but didn't improve


class TrainingFrameworkType(str, Enum):
    OTX = "otx"  # OpenVINO Training Extensions
    THIRD_PARTY = "third_party"  # 3rd party (non-Intel) framework
    GETI_VPS = "geti_vps"  # Geti visual prompting service


class ModelDeprecationStatus(Enum):
    """Status of a model with respect to the deprecation process."""

    ACTIVE = auto()  # Model is fully supported, models can be trained
    OBSOLETE = auto()  # Model is no longer supported, models can be still viewed but not trained

    def __str__(self) -> str:
        """Returns the name of the model status."""
        return str(self.name)


@dataclass(frozen=True)
class TrainingFramework:
    """Identifier of the framework used to train the model"""

    type: TrainingFrameworkType
    version: str

    @classmethod
    def get_default(cls) -> "TrainingFramework":
        trainer_version = os.environ.get("DEFAULT_TRAINER_VERSION")
        if not trainer_version:
            raise RuntimeError("Missing environment variable 'DEFAULT_TRAINER_VERSION'")
        return cls(type=TrainingFrameworkType.OTX, version=trainer_version)


class ModelPurgeInfo:
    """
    Class to hold model purge information.

    :param is_purged: Boolean indicating if the model is purged
    :param purge_time: Timestamp when the model was purged
    :param user_uid: User ID that purged the model
    """

    def __init__(
        self, is_purged: bool = False, purge_time: datetime.datetime | None = None, user_uid: str | None = None
    ):
        self.is_purged = is_purged
        self.purge_time = purge_time
        self.user_uid = user_uid


class ModelPrecision(IntEnum):
    """Represents the ModelPrecision of a Model."""

    INT4 = auto()
    INT8 = auto()
    FP16 = auto()
    FP32 = auto()

    def __str__(self):
        """String."""
        return self.name


class ModelFormat(IntEnum):
    """Indicate the format of the model."""

    OPENVINO = auto()
    BASE_FRAMEWORK = auto()
    ONNX = auto()


class ModelOptimizationType(IntEnum):
    """Represents optimization type that is used to optimize the model."""

    NONE = auto()
    MO = auto()
    POT = auto()
    ONNX = auto()


class OptimizationMethod(IntEnum):
    """Represents optimization method that is used to optimize the model."""

    FILTER_PRUNING = auto()
    QUANTIZATION = auto()


class Model(PersistentEntity):
    """
    A model represents a supervised (trained) model that is persisted.

    What is persisted depends on the model but are usually its parameters (e.g. deep learning weights).

    Examples are a deep learning model, regression model or a SVM model.

    To be able to use the model for predictions, the model has to be loaded in its corresponding task,
    which is defined through `task_node`.

    :param id_: the ID of this model
    :param model_storage: the model storage to which the model belongs
    :param train_dataset: the dataset which is used to train this model
    :param configuration: configuration used to generate this model
    :param creation_date: the creation_date time of model creation
    :param performance: performance of the model. See :class:`Performance`
    :param previous_revision: the model that has the most immediate connection to the model. For example,
        if this model is to store finetuned model, the previous_revision is the initial model of the finetuning process;
        if this model is to store MO export of an NNCF model, the previous_revision points to NNCF model output.
    :param previous_trained_revision: the model trained in the original framework (e.g., Pytorch, TF) that has the most
        immediate connection to the model. For example, if this model is to store finetuned model, the
        previous_trained_revision is the initial model of the finetuning process; if this model is to store POT/NNCF
        model, the previous_trained_revision points to the Pytorch model output.
    :param tags: can be used to store additional parameters, but can also be used to filter on in the ModelRepo.
        For example, a task that can switch backbones, can use this filter to find Model entities that belong to
        the network architecture loaded.
    :param data_source_dict: Source that can fetch de bytes data of the model, either direct bytes or a DataSource
        Usually this directory contains a model (e.g., weights) and a configuration file (e.g., architecture structure).
    :param training_framework: Identifier of the training framework from which the model was generated
    :param model_status: Indicates the status of the model's last training round.
    :param model_format: Indicates the format of the model, for example, OpenVino, ONNX, etc.
    :param has_xai_head: bool indicating if model outputs explainable AI features, for exampe, a saliency map
    :param training_duration: the training duration in seconds
    :param precision: List of precisions used to quantize the model, e.g. [FP16, INT8]
    :param latency: How much latency there is between start of inference and result (ms)
    :param fps_throughput: How many frames per second this model can output
    :param target_device: Target device on which the model will be deployed, e.g. CPU
    :param target_device_type: Type of the device on which the model will be deployed. e.g. Intel i9-10980XE
    :param optimization_type: Used type to optimize the model, e.g. NNCF.
    :param optimization_methods: List of optimization methods used to optimize the model, e.g. [Pruning]
    :param optimization_objectives: dictionary with optimization objectives and their
        values, e.g. {"bit_complexity_ratio": "0.3"}
    :param performance_improvement: dict with float indicating how much the performance has improved, e.g. (???)
    :param model_size_reduction: float indicating how much the model size has been reduced, e.g. byte/percentage/other??
    :param exportable_code_adapter: Adapter that contains a deployed model file, either as raw bytes or a DataSource,
    :param size: the size of the model in bytes
    :param version: version of the model
    :param purge_info: Object containing model purge information.
    """

    def __init__(  # noqa: PLR0913
        self,
        project: "Project",
        model_storage: ModelStorage,
        train_dataset: "Dataset",
        configuration: ModelConfiguration,
        id_: ID,
        *,
        creation_date: datetime.datetime | None = None,
        performance: Performance | None = None,
        previous_trained_revision: Optional["Model"] = None,
        previous_revision: Optional["Model"] = None,
        tags: list[str] | None = None,
        data_source_dict: Mapping[str, DataSource | bytes] | None = None,
        training_framework: TrainingFramework | None = None,
        model_status: ModelStatus = ModelStatus.SUCCESS,
        model_format: ModelFormat = ModelFormat.OPENVINO,
        has_xai_head: bool = False,
        training_duration: float = 0.0,
        training_job_duration: float = 0.0,
        precision: list[ModelPrecision] | None = None,
        latency: int = 0,
        fps_throughput: int = 0,
        target_device: TargetDevice = TargetDevice.CPU,
        target_device_type: str | None = None,
        optimization_type: ModelOptimizationType = ModelOptimizationType.NONE,
        optimization_methods: list[OptimizationMethod] | None = None,
        optimization_objectives: dict[str, str] | None = None,
        performance_improvement: dict[str, float] | None = None,
        model_size_reduction: float = 0.0,
        exportable_code_adapter: ExportableCodeAdapter | None = None,
        size: int | None = None,
        version: int = 1,
        ephemeral: bool = True,
        purge_info: ModelPurgeInfo | None = None,
    ) -> None:
        if data_source_dict is None:
            data_source_dict = {}
        model_adapters = {key: ModelAdapter(val) for key, val in data_source_dict.items()}
        id_ = ID() if id_ is None else id_
        PersistentEntity.__init__(self, id_=id_, ephemeral=ephemeral)

        performance = NullPerformance() if performance is None else performance
        creation_date = now() if creation_date is None else creation_date

        optimization_methods = [] if optimization_methods is None else optimization_methods
        optimization_objectives = {} if optimization_objectives is None else optimization_objectives
        performance_improvement = {} if performance_improvement is None else performance_improvement

        tags = [] if tags is None else tags
        precision = [ModelPrecision.FP32] if precision is None else precision

        self.creation_date = creation_date
        self.train_dataset = train_dataset
        self.previous_trained_revision = previous_trained_revision
        self.previous_revision = previous_revision
        self.version = version
        self.tags = tags
        self.model_format = model_format
        self.performance = performance
        self.training_duration = training_duration
        self.configuration = configuration
        self.__model_adapters = model_adapters
        self.__exportable_code_adapter = exportable_code_adapter
        self.model_adapters_to_delete: list[ModelAdapter] = []
        self.precision = precision
        self.latency = latency
        self.fps_throughput = fps_throughput
        self.target_device = target_device
        self.target_device_type = target_device_type
        self.optimization_type = optimization_type
        self.optimization_methods = optimization_methods
        self.optimization_objectives = optimization_objectives
        self.performance_improvement = performance_improvement
        self.model_size_reduction = model_size_reduction
        self.has_xai_head = has_xai_head

        self.__project_adapter: IAdapter[Project] = ReferenceAdapter(project)
        self.__train_dataset_adapter: IAdapter[Dataset] = ReferenceAdapter(train_dataset)
        previous_trained_revision = NullModel() if previous_trained_revision is None else previous_trained_revision
        self.__previous_trained_revision_adapter: IAdapter[Model] = ReferenceAdapter(previous_trained_revision)
        previous_revision = NullModel() if previous_revision is None else previous_revision

        self.__previous_revision_adapter: IAdapter[Model] = ReferenceAdapter(previous_revision)
        self.__training_framework = (
            TrainingFramework.get_default() if training_framework is None else training_framework
        )
        self.model_storage = model_storage
        self.model_status = model_status
        self.__size = size
        self.training_job_duration = training_job_duration
        self.purge_info = ModelPurgeInfo() if purge_info is None else purge_info

    @classmethod
    def with_adapters(  # noqa: PLR0913
        cls,
        project_adapter: IAdapter["Project"],
        train_dataset_adapter: IAdapter["Dataset"],
        previous_trained_revision_adapter: IAdapter["Model"],
        previous_revision_adapter: IAdapter["Model"],
        model_storage: ModelStorage,
        configuration: ModelConfiguration,
        _id: ID,
        *,
        creation_date: datetime.datetime | None = None,
        performance: Performance | None = None,
        tags: list[str] | None = None,
        data_source_dict: Mapping[str, DataSource | bytes] | None = None,
        training_framework: TrainingFramework | None = None,
        model_status: ModelStatus = ModelStatus.SUCCESS,
        model_format: ModelFormat = ModelFormat.OPENVINO,
        training_duration: float = 0.0,
        training_job_duration: float = 0.0,
        precision: list[ModelPrecision] | None = None,
        has_xai_head: bool = False,
        latency: int = 0,
        fps_throughput: int = 0,
        target_device: TargetDevice = TargetDevice.CPU,
        target_device_type: str | None = None,
        optimization_type: ModelOptimizationType = ModelOptimizationType.NONE,
        optimization_methods: list[OptimizationMethod] | None = None,
        optimization_objectives: dict[str, str] | None = None,
        performance_improvement: dict[str, float] | None = None,
        model_size_reduction: float = 0.0,
        exportable_code_adapter: ExportableCodeAdapter | None = None,
        size: int | None = None,
        version: int = 1,
        ephemeral: bool = True,
    ):
        """Instantiate the Model with adapters for the project, train dataset, previous revision and previous trained
        revision."""
        from iai_core_py.entities.datasets import NullDataset
        from iai_core_py.entities.project import NullProject

        inst = cls(
            project=NullProject(),
            train_dataset=NullDataset(),
            previous_trained_revision=NullModel(),
            previous_revision=NullModel(),
            configuration=configuration,
            model_storage=model_storage,
            creation_date=creation_date,
            performance=performance,
            tags=tags,
            data_source_dict=data_source_dict,
            training_framework=training_framework,
            model_status=model_status,
            model_format=model_format,
            training_duration=training_duration,
            training_job_duration=training_job_duration,
            precision=precision,
            has_xai_head=has_xai_head,
            latency=latency,
            fps_throughput=fps_throughput,
            target_device=target_device,
            target_device_type=target_device_type,
            optimization_type=optimization_type,
            optimization_methods=optimization_methods,
            optimization_objectives=optimization_objectives,
            performance_improvement=performance_improvement,
            model_size_reduction=model_size_reduction,
            exportable_code_adapter=exportable_code_adapter,
            size=size,
            version=version,
            id_=_id,
            ephemeral=ephemeral,
        )
        inst.__project_adapter = project_adapter
        inst.__train_dataset_adapter = train_dataset_adapter
        inst.__previous_trained_revision_adapter = previous_trained_revision_adapter
        inst.__previous_revision_adapter = previous_revision_adapter
        return inst

    @property
    def size(self) -> int:
        """Returns the model size in bytes."""
        if self.__size is None or self.__size == 0:
            computed_size = 0
            for model_adapter in self.model_adapters.values():
                data_source = model_adapter.data_source
                computed_size += data_source.size if isinstance(data_source, DataSource) else len(data_source)
            self.__size = computed_size
        return self.__size

    @size.setter
    def size(self, value: int) -> None:
        """Sets the size of the model"""
        self.__size = value

    @property
    def training_framework(self) -> TrainingFramework:
        return self.__training_framework

    @property
    def model_deprecation_status(self) -> ModelDeprecationStatus:
        """Returns the deprecation status of the model."""

        # Versions older than 2.0 are obsolete and no longer supported for training and optimisation.
        if tuple(self.training_framework.version.split(".")) < ("2", "0"):
            return ModelDeprecationStatus.OBSOLETE
        return ModelDeprecationStatus.ACTIVE

    def get_project(self) -> "Project":
        """Get the project connected to the model"""
        return self.__project_adapter.get()

    @property
    def project_id(self) -> ID:
        """Get the ID of the project connected to the model"""
        return self.__project_adapter.id_

    @property
    def model_storage_identifier(self) -> ModelStorageIdentifier:
        """Get the identifier of the model storage containing this model"""
        return self.model_storage.identifier

    @property
    def exportable_code_adapter(self) -> ExportableCodeAdapter | None:
        """Returns the exportable code adapter."""
        return self.__exportable_code_adapter

    @property
    def exportable_code(self) -> bytes | None:
        """Get the exportable_code from the exportable code adapter."""
        if self.__exportable_code_adapter is not None:
            return self.__exportable_code_adapter.data
        return None

    @exportable_code.setter
    def exportable_code(self, data: bytes | DataSource):
        """Set the exportable code using the exportable code adapter."""
        self.__exportable_code_adapter = ExportableCodeAdapter(data_source=data)

    def get_data(self, key: str) -> bytes:
        """
        Fetches byte data for a certain model.

        :param key: key to fetch data for
        :returns: bytes: data for the key.
        """
        return self.__model_adapters[key].data

    def set_data(self, key: str, data: bytes | DataSource, skip_deletion: bool = False) -> None:
        """Sets the data for a specified key, either from a binary blob or from a data source.

        If the key already exists it appends existing data url to a list of urls that will be removed upon saving the
        model. Skip deletion parameter should only be true if replacing bytes data with a file.
        """
        if not skip_deletion:
            self.delete_data(key)
        self.__model_adapters[key] = ModelAdapter(data)

    def delete_data(self, key: str) -> None:
        """This function is used to delete data sources that are on the filesystem.

        If the key exists the model adapter will be appended to a list of model adapter that will be removed once the
        model is saved by the repo. Note that an optimized model must contain at least 1 DataSource otherwise you are
        left with an invalid optimized model.
        """
        if key in self.__model_adapters:
            self.model_adapters_to_delete.append(self.__model_adapters[key])
            del self.__model_adapters[key]

    @property
    def model_adapters(self) -> dict[str, ModelAdapter]:
        """Returns the dictionary of model adapters for each data key."""
        return self.__model_adapters

    def is_optimized(self) -> bool:
        """Returns a boolean indicating if the model has been optimized or not."""
        return self.optimization_type != ModelOptimizationType.NONE

    def get_train_dataset(self) -> "Dataset":
        """Get the dataset used to train the model"""
        return self.__train_dataset_adapter.get()

    def set_train_dataset(self, value: "Dataset") -> None:
        """Set the dataset used to train the model"""
        self.__train_dataset_adapter = ReferenceAdapter(value)

    @property
    def train_dataset_id(self) -> ID:
        """Get the ID of the dataset used to train the model"""
        return self.__train_dataset_adapter.id_

    def get_previous_trained_revision(self) -> "Model":
        """Get the previous trained revision for this model"""
        return self.__previous_trained_revision_adapter.get()

    def set_previous_trained_revision(self, value: "Model") -> None:
        """Set the previous trained revision for this model"""
        self.__previous_trained_revision_adapter = ReferenceAdapter(value)

    def get_base_model(self) -> "Model":
        """Get the base framework model used to train this model"""
        if self.optimization_type == ModelOptimizationType.NONE:
            return self
        return self.get_previous_trained_revision()

    @property
    def previous_trained_revision_id(self) -> ID:
        """Get the ID of the previous trained revision for this model"""
        return self.__previous_trained_revision_adapter.id_

    def get_previous_revision(self) -> "Model":
        """Get the previous revision for this model"""
        return self.__previous_revision_adapter.get()

    def set_previous_revision(self, value: "Model") -> None:
        """Set the previous revision for this model"""
        self.__previous_revision_adapter = ReferenceAdapter(value)

    @property
    def previous_revision_id(self) -> ID:
        """Set the ID of the previous revision for this model"""
        return self.__previous_revision_adapter.id_

    def get_label_schema(self) -> LabelSchema:
        """Get the label schema used by the model"""
        return self.configuration.get_label_schema()

    @property
    def label_schema_id(self) -> ID:
        """Get the ID of the label schema used by the model"""
        return self.configuration.label_schema_id

    def is_failed(self) -> bool:
        """
        Find whether this model is a residual from a failed training job.

        :return: bool indicating if the model results from a failed training
        """
        return self.model_status == ModelStatus.FAILED

    def is_pending(self) -> bool:
        """
        Find whether the final state for the model is pending yet, because the model
        there is an unfinished job (e.g  training, optimization or evaluation) for it.

        :return: bool indicating if the model status has not reached a final state yet
        """
        return self.model_status in (
            ModelStatus.NOT_READY,
            ModelStatus.TRAINED_NO_STATS,
        )

    @property
    def weight_paths(self) -> dict[str, str]:
        """Returns the filename where the data is stored in the binary repo for each data key.

        Note that this function will raise an error if the model was not saved to a database.
        """
        return {
            key: model_adapter.data_source.binary_filename  # type: ignore[union-attr]
            for key, model_adapter in self.model_adapters.items()
            if model_adapter.from_file_storage
        }

    def has_trained_weights(self) -> bool:
        """
        Find whether the model has valid trained weights, regardless of their quality.

        :return: bool indicating whether the model contains trained weights
        """
        if self.purge_info.is_purged:
            return False

        return self.model_status in (
            ModelStatus.TRAINED_NO_STATS,
            ModelStatus.NOT_IMPROVED,
            ModelStatus.SUCCESS,
        )

    def is_improved(self) -> bool:
        """
        Find whether the evaluated model has a better accuracy than its previous.

        :return: bool indicating if the model is an improvement
        """
        return self.model_status == ModelStatus.SUCCESS

    def is_successful(self) -> bool:
        """
        Find whether the model has undergone a full and successful training job.

        Note: although in the current implementation this method an alias of
        :meth:`is_improved`, the definition of 'improved' is weaker than 'successful'.
        In other words, in the future we may introduce extra conditions that a model
        must satisfy to be considered successful, in addition to the 'improved' one.

        :return: bool indicating if the model is successful
        """
        return self.model_status == ModelStatus.SUCCESS

    def __repr__(self) -> str:
        return (
            f"Model({self.id_}, project_id={self.project_id}, model_storage_id={self.model_storage.id_}, "
            f"creation_date='{self.creation_date}')"
        )

    def __eq__(self, other: object):
        if not isinstance(other, Model):
            return False
        return self.id_ == other.id_


class NullModel(Model):
    """Representation of a model 'model not found'"""

    def __init__(self) -> None:
        from iai_core_py.entities.datasets import NullDataset
        from iai_core_py.entities.project import NullProject

        super().__init__(
            project=NullProject(),
            model_storage=NullModelStorage(),
            train_dataset=NullDataset(),
            configuration=ModelConfiguration(NullHyperParameters().data, NullLabelSchema()),
            id_=ID(),
            creation_date=datetime.datetime.min.replace(tzinfo=datetime.timezone.utc),
            performance=NullPerformance(),
            previous_trained_revision=self,
            previous_revision=self,
            data_source_dict={"NullModel.bin": b"data"},
            training_framework=TrainingFramework(type=TrainingFrameworkType.OTX, version="null"),
            model_status=ModelStatus.NOT_IMPROVED,
            model_format=ModelFormat.OPENVINO,
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullModel()"
