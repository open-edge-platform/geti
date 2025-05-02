# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, cast

from communication.rest_views.label_rest_views import LabelRESTViews
from communication.rest_views.performance_rest_views import PerformanceRESTViews

from geti_telemetry_tools import unified_tracing
from geti_types import ID
from iai_core_py.algorithms.visual_prompting import VISUAL_PROMPTING_MODEL_TEMPLATE_ID
from iai_core_py.entities.metrics import Performance
from iai_core_py.entities.model import Model, ModelFormat, ModelOptimizationType
from iai_core_py.entities.model_storage import ModelStorage
from iai_core_py.repos.model_repo import ModelStatusFilter

if TYPE_CHECKING:
    from iai_core_py.configuration.elements.optimization_parameters import POTOptimizationParameters

ACTIVE_MODEL = "active_model"
ARCHITECTURE = "architecture"
CREATION_DATE = "creation_date"
DATASET_STORAGE_ID = "dataset_storage_id"
DATASET_REVISION_ID = "dataset_revision_id"
FPS_THROUGHPUT = "fps_throughput"
HAS_XAI_HEAD = "has_xai_head"
ID_ = "id"
IS_FILTER_PRUNING_ENABLED = "is_filter_pruning_enabled"
IS_FILTER_PRUNING_SUPPORTED = "is_filter_pruning_supported"
IS_NNCF_SUPPORTED = "is_nncf_supported"
IS_PURGED = "is_purged"
LABEL_SCHEMA_IN_SYNC = "label_schema_in_sync"
LABELS = "labels"
LATENCY = "latency"
LIFECYCLE_STAGE = "lifecycle_stage"
MODELS = "models"
MODEL_FORMAT = "model_format"
MODEL_STATUS = "model_status"
MODEL_TEMPLATE_ID = "model_template_id"
MODEL_GROUP_ID = "model_group_id"
N_FRAMES = "n_frames"
N_IMAGES = "n_images"
N_VIDEOS = "n_videos"
N_SAMPLES = "n_samples"
NAME = "name"
OPTIMIZATION_OBJECTIVES = "optimization_objectives"
OPTIMIZATION_METHODS = "optimization_methods"
OPTIMIZATION_TYPE = "optimization_type"
OPTIMIZED_MODELS = "optimized_models"
PERFORMANCE = "performance"
PRECISION = "precision"
PREVIOUS_REVISION_ID = "previous_revision_id"
PREVIOUS_TRAINED_REVISION_ID = "previous_trained_revision_id"
PURGE_TIME = "purge_time"
PURGE_INFO = "purge_info"
SIZE = "size"
SCORE_UP_TO_DATE = "score_up_to_date"
TARGET_DEVICE = "target_device"
TARGET_DEVICE_TYPE = "target_device_type"
TASK_ID = "task_id"
TOTAL_DISK_SIZE = "total_disk_size"
TRAINING_DATASET_INFO = "training_dataset_info"
TRAINING_FRAMEWORK = "training_framework"
TYPE = "type"
USER_UID = "user_uid"
VERSION = "version"
CONFIGURATIONS = "configurations"
LEARNING_APPROACH = "learning_approach"


class LearningApproach(Enum):
    """
    Enum containing model's learning approaches

    FULLY_SUPERVISED: model is trained on a dataset in fully supervised way. Used by regular Geti models.
    ONE_SHOT: one-shot learning, model is trained on a single example. Used by visual prompting models.
    """

    FULLY_SUPERVISED = auto()
    ONE_SHOT = auto()


@dataclass
class ModelRestInfo:
    """
    Class to store model info in that is gathered before mapping the model to rest representation

    :param model: Model for which info is gathered
    :param performance: Performance of the model
    :param is_label_schema_in_sync: If the label schema is in sync for the model
    """

    model: Model
    performance: Performance
    is_label_schema_in_sync: bool


class ModelRESTViews:
    """
    This class maps presents Model entities as REST and can interpret REST views to entities
    """

    @staticmethod
    @unified_tracing
    def model_storage_to_rest(
        model_storage: ModelStorage,
        per_model_info: Sequence[ModelRestInfo],
        task_node_id: ID,
        active_model: Model,
        include_lifecycle_stage: bool = False,  # TODO CVS-159532 remove this parameter
    ) -> dict[str, Any]:
        """
        Converts a ModelStorage to a REST representation. Checks whether the model is the active model by fetching the
        active model and checking if it is the same model. Checks whether the score for the model is up to date by
        comparing the train dataset of the model with that of the newest model in the repo.

        :param model_storage: ModelStorage to convert to rest representation
        :param per_model_info: Model info object containing data that will be mapped to a rest view
        :param task_node_id: The id of the task node that makes use of this ModelStorage.
        :param active_model: The current active model in the model storage.
        :param include_lifecycle_stage: Whether to include the lifecycle stage in the rest view
        :return: dictionary with REST representation of the model storage
        """
        models_rest_list: list[dict] = []
        for model_info in per_model_info:
            model = model_info.model
            models_rest_list.append(
                {
                    ID_: str(model.id_),
                    NAME: model.model_storage.name,
                    CREATION_DATE: model.creation_date.isoformat(),
                    SCORE_UP_TO_DATE: True,  # this field is deprecated, value is always 'True' and should not be used
                    ACTIVE_MODEL: model == active_model,
                    SIZE: model.size,
                    PERFORMANCE: PerformanceRESTViews.performance_to_rest(model_info.performance),
                    LABEL_SCHEMA_IN_SYNC: model_info.is_label_schema_in_sync,
                    VERSION: model.version,
                    PURGE_INFO: {
                        IS_PURGED: model.purge_info.is_purged,
                        PURGE_TIME: model.purge_info.purge_time.isoformat()
                        if model.purge_info.purge_time is not None
                        else None,
                        USER_UID: model.purge_info.user_uid,
                    },
                    LIFECYCLE_STAGE: model.model_deprecation_status.name.lower(),
                }
            )

        rest_view = {
            ID_: str(model_storage.id_),
            NAME: model_storage.name,
            MODEL_TEMPLATE_ID: model_storage.model_template.model_template_id,
            TASK_ID: str(task_node_id),
            MODELS: models_rest_list,
            LEARNING_APPROACH: (
                LearningApproach.ONE_SHOT.name.lower()
                if model_storage.model_template.model_template_id == VISUAL_PROMPTING_MODEL_TEMPLATE_ID
                else LearningApproach.FULLY_SUPERVISED.name.lower()
            ),
        }
        if include_lifecycle_stage:  # TODO CVS-159532 output lyfecycle_stage unconditionally
            rest_view[LIFECYCLE_STAGE] = model_storage.model_template.model_status.name.lower()
        return rest_view

    @staticmethod
    @unified_tracing
    def model_to_rest(
        model: Model,
        model_performance: Performance,
        is_label_schema_in_sync: bool,
        task_node_id: ID,
        active_model: Model,
    ) -> dict[str, Any]:
        """
        Return the (non-detailed) model rest view, including the task ID and model storage ID.

        :param model: Model to be converted to rest view
        :param model_performance: Performance for this model
        :param is_label_schema_in_sync: Boolean indicating whether or not this model is based on the latest schema
        :param task_node_id: Relevant task node for the model
        :param active_model: Current active model for the task node
        :return: Rest view for the provided model
        """
        return {
            ID_: str(model.id_),
            NAME: model.model_storage.name,
            CREATION_DATE: model.creation_date.isoformat(),
            SCORE_UP_TO_DATE: True,  # Note: this field is deprecated, value is always 'True' and should not be used
            ACTIVE_MODEL: model == active_model,
            SIZE: model.size,
            PERFORMANCE: PerformanceRESTViews.performance_to_rest(model_performance),
            LABEL_SCHEMA_IN_SYNC: is_label_schema_in_sync,
            VERSION: model.version,
            MODEL_GROUP_ID: model.model_storage.id_,
            TASK_ID: task_node_id,
            PURGE_INFO: {
                IS_PURGED: model.purge_info.is_purged,
                PURGE_TIME: model.purge_info.purge_time.isoformat()
                if model.purge_info.purge_time is not None
                else None,
                USER_UID: model.purge_info.user_uid,
            },
            LIFECYCLE_STAGE: model.model_deprecation_status.name.lower(),
        }

    @staticmethod
    @unified_tracing
    def model_info_to_rest(
        model: Model,
        model_performance: Performance,
        is_label_schema_in_sync: bool,
        dataset_storage_id: ID,
        dataset_counts: dict[str, int],
        optimized_per_model_performance: Sequence[tuple[Model, Performance]],
        total_disk_size: int,
    ) -> dict:
        """
        Converts a list of optimized models and a trained model to one dict representation. This is a more detailed
        view than the simpler model_to_rest.

        :param model: Model to convert to rest
        :param model_performance: The performance associated with the model
        :param is_label_schema_in_sync: is label schema of the model in sync with latest in task node
        :param dataset_storage_id: ID of the dataset storage model is trained on
        :param dataset_counts: dataset storage count of items
        :param optimized_per_model_performance: Optimized models related to the model
            with the related performance as a tuple
        :param total_disk_size: Total disk size of the model and its related binaries
        :return: dictionary with REST representation of the model
        """
        label_schema = model.configuration.get_label_schema()
        labels = label_schema.get_labels(include_empty=True)
        result = {
            ID_: model.id_,
            NAME: model.model_storage.name,
            ARCHITECTURE: model.model_storage.model_template.name,
            VERSION: model.version,
            CREATION_DATE: model.creation_date.isoformat(),
            SIZE: model.size,
            SCORE_UP_TO_DATE: True,  # Note: this field is deprecated, value is always 'True' and should not be used
            FPS_THROUGHPUT: model.fps_throughput,
            LATENCY: model.latency,
            PERFORMANCE: PerformanceRESTViews.performance_to_rest(model_performance),
            LABEL_SCHEMA_IN_SYNC: is_label_schema_in_sync,
            PRECISION: [precision.name for precision in model.precision],
            TARGET_DEVICE: model.target_device.name,
            TARGET_DEVICE_TYPE: model.target_device_type,
            OPTIMIZED_MODELS: [
                ModelRESTViews.optimized_model_to_rest(optimized_model, performance)
                for optimized_model, performance in optimized_per_model_performance
            ],
            LABELS: [LabelRESTViews.label_to_rest(label, label_schema) for label in labels],  # type: ignore
            TRAINING_DATASET_INFO: {
                DATASET_STORAGE_ID: dataset_storage_id,
                DATASET_REVISION_ID: model.train_dataset_id,
                N_SAMPLES: dataset_counts.get(N_SAMPLES),
                N_IMAGES: dataset_counts.get(N_IMAGES),
                N_VIDEOS: dataset_counts.get(N_VIDEOS),
                N_FRAMES: dataset_counts.get(N_FRAMES),
            },
            TRAINING_FRAMEWORK: {TYPE: model.training_framework.type.value, VERSION: model.training_framework.version},
            PURGE_INFO: {
                IS_PURGED: model.purge_info.is_purged,
                PURGE_TIME: model.purge_info.purge_time.isoformat()
                if model.purge_info.purge_time is not None
                else None,
                USER_UID: model.purge_info.user_uid,
            },
            TOTAL_DISK_SIZE: total_disk_size,
            LEARNING_APPROACH: (
                LearningApproach.ONE_SHOT.name.lower()
                if model.model_storage.model_template.model_template_id == VISUAL_PROMPTING_MODEL_TEMPLATE_ID
                else LearningApproach.FULLY_SUPERVISED.name.lower()
            ),
            LIFECYCLE_STAGE: model.model_deprecation_status.name.lower(),
        }

        if model.previous_revision_id is not None:
            result[PREVIOUS_REVISION_ID] = str(model.previous_revision_id)
        if model.previous_trained_revision_id is not None:
            result[PREVIOUS_TRAINED_REVISION_ID] = str(model.previous_trained_revision_id)

        return result

    @staticmethod
    @unified_tracing
    def optimized_model_to_rest(optimized_model: Model, performance: Performance) -> dict:
        """
        Converts one optimized model to a dict representation.

        :param optimized_model: The optimized model to convert to rest
        :param performance: The performance of the optimized model
        :return: dictionary with REST representation of the optimized model
        """
        precision: list[str] = (
            []
            if optimized_model.model_status.name not in ModelStatusFilter.TRAINED.value
            else [precision.name for precision in optimized_model.precision]
        )
        model_format = (
            "OpenVINO" if optimized_model.model_format is ModelFormat.OPENVINO else optimized_model.model_format.name
        )
        optimization_type = optimized_model.optimization_type.name
        with_xai = "with XAI head" if optimized_model.has_xai_head else ""
        precision_text = precision[0] if precision else ""
        name = " ".join(
            filter(
                None,
                [
                    optimized_model.model_storage.name,
                    model_format,
                    precision_text,
                    with_xai,
                ],
            )
        )
        result = {
            ID_: optimized_model.id_,
            NAME: name,
            VERSION: optimized_model.version,
            CREATION_DATE: optimized_model.creation_date.isoformat(),
            MODEL_FORMAT: model_format,
            PRECISION: precision,
            HAS_XAI_HEAD: optimized_model.has_xai_head,
            TARGET_DEVICE: optimized_model.target_device.name,
            TARGET_DEVICE_TYPE: optimized_model.target_device_type,
            PERFORMANCE: PerformanceRESTViews.performance_to_rest(performance),
            SIZE: optimized_model.size,
            LATENCY: optimized_model.latency,
            FPS_THROUGHPUT: optimized_model.fps_throughput,
            OPTIMIZATION_TYPE: optimization_type,
            OPTIMIZATION_OBJECTIVES: optimized_model.optimization_objectives,
            MODEL_STATUS: optimized_model.model_status.name,
            CONFIGURATIONS: [],
            LIFECYCLE_STAGE: optimized_model.model_deprecation_status.name.lower(),
        }

        configurations: list[dict] = []
        if optimized_model.optimization_type == ModelOptimizationType.POT:
            model_pot_settings = cast(
                "POTOptimizationParameters",
                optimized_model.configuration.configurable_parameters.pot_parameters,  # type: ignore[attr-defined]
            )
            if hasattr(model_pot_settings, "stat_subset_size"):
                stat_subset_size = {
                    "name": "sample_size",
                    "value": model_pot_settings.stat_subset_size,
                }
                configurations.append(stat_subset_size)

        result[CONFIGURATIONS] = configurations

        if optimized_model.previous_revision_id != ID():
            result[PREVIOUS_REVISION_ID] = str(optimized_model.previous_revision_id)
        if optimized_model.previous_trained_revision_id != ID():
            result[PREVIOUS_TRAINED_REVISION_ID] = str(optimized_model.previous_trained_revision_id)
        if optimized_model.optimization_methods is not None:
            result[OPTIMIZATION_METHODS] = [method.name for method in optimized_model.optimization_methods]

        return result
