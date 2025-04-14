# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Constants and enums for Geti-OTX interface adapters."""

from enum import Enum

from sc_sdk.entities.label_schema import LabelSchema

from jobs_common_extras.evaluation.utils.classification_utils import get_cls_inferencer_configuration

BASE_FRAMEWORK_KEY = "weights.pth"
OPENVINO_XML_KEY = "openvino.xml"
OPENVINO_BIN_KEY = "openvino.bin"
ONNX_KEY = "model.onnx"
CONFIG_JSON_KEY = "config.json"
LABEL_SCHEMA_KEY = "label_schema.json"


class MLFlowRunStatus(str, Enum):
    """Enum for MLFlow Run Status.

    Please see the source from
    https://mlflow.org/docs/latest/_modules/mlflow/entities/run_status.html
    """

    RUNNING = "RUNNING"
    SCHEDULED = "SCHEDULED"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    KILLED = "KILLED"


class MLFlowLifecycleStage(str, Enum):
    """Enum for MLFlow Run LifecycleStage.

    Please see the source from
    https://mlflow.org/docs/latest/_modules/mlflow/entities/lifecycle_stage.html
    """

    ACTIVE = "active"
    DELETED = "deleted"


class ClsSubTaskType(str, Enum):
    """Auxilary enum to discriminate classification tasks in Geti.

    This is because Geti has no distinguishable mark
    for multi-class, multi-label, and hiarchical classification tasks.
    It is only possible to prove `LabelSchema` to distinguish them.
    This should be improved in the future.
    """

    MULTI_CLASS_CLS = "MULTI_CLASS_CLS"
    MULTI_LABEL_CLS = "MULTI_LABEL_CLS"
    H_LABEL_CLS = "H_LABEL_CLS"

    @classmethod
    def create_from_label_schema(cls, label_schema: LabelSchema) -> "ClsSubTaskType":
        """Create this enum from label_schema.

        :param label_schema: Geti label schema
        :return: This enum
        """
        config = get_cls_inferencer_configuration(label_schema=label_schema)

        if config.get("hierarchical", False):
            return ClsSubTaskType.H_LABEL_CLS
        if config.get("multilabel", False):
            return ClsSubTaskType.MULTI_LABEL_CLS

        return ClsSubTaskType.MULTI_CLASS_CLS
