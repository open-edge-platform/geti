# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""Constants and statically defined information"""

from enum import Enum


class AnnotationType(str, Enum):
    """Annotation types supported by Geti"""

    LABEL = "label"
    MULTI_LABEL = "multi label"
    HIERARCHICAL_LABEL = "hierarchical label"
    BOUNDING_BOX = "bounding box"
    ORIENTED_BOUNDING_BOX = "oriented bounding box"
    ELLIPSE = "ellipse"
    POLYGON = "polygon"
    ANOMALY_LABEL = "anomaly label"


class ExportedDatasetFormat(str, Enum):
    """Dataset formats supported by Geti"""

    DATUMARO = "Datumaro"
    COCO = "COCO"
    VOC = "VOC"
    YOLO = "YOLO"


class JobType(str, Enum):
    """Job types supported by Geti. The enum values match the names adopted by the API"""

    TRAINING = "train"
    OPTIMIZATION = "optimize_pot"
    EVALUATION = "test"
    DATASET_IMPORT_TO_NEW_PROJECT_PREPARATION = "prepare_import_to_new_project"
    DATASET_IMPORT_TO_EXISTING_PROJECT_PREPARATION = "prepare_import_to_existing_project"
    DATASET_IMPORT_TO_NEW_PROJECT = "perform_import_to_new_project"
    DATASET_IMPORT_TO_EXISTING_PROJECT = "perform_import_to_existing_project"
    DATASET_EXPORT = "export_dataset"
    PROJECT_IMPORT = "import_project"
    PROJECT_EXPORT = "export_project"


class JobState(str, Enum):
    """Job states supported by Geti. The enum values match the names adopted by the API"""

    RUNNING = "running"
    FINISHED = "finished"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskType(str, Enum):
    """Task types supported by Geti. The enum values match the names adopted by the API"""

    CLASSIFICATION = "classification"
    DETECTION = "detection"
    ROTATED_DETECTION = "rotated_detection"
    INSTANCE_SEGMENTATION = "instance_segmentation"
    SEGMENTATION = "segmentation"
    ANOMALY = "anomaly"
    KEYPOINT_DETECTION = "keypoint_detection"


class ProjectType(str, Enum):
    """Project types supported by Geti"""

    MULTICLASS_CLASSIFICATION = "multiclass classification"
    MULTILABEL_CLASSIFICATION = "multilabel classification"
    HIERARCHICAL_CLASSIFICATION = "hierarchical classification"
    DETECTION = "detection"
    ORIENTED_DETECTION = "oriented detection"
    INSTANCE_SEGMENTATION = "instance segmentation"
    SEMANTIC_SEGMENTATION = "semantic segmentation"
    ANOMALY_DETECTION = "anomaly detection"
    KEYPOINT_DETECTION = "keypoint detection"
    TASK_CHAIN_DETECTION_CLASSIFICATION = "detection > classification"
    TASK_CHAIN_DETECTION_SEGMENTATION = "detection > segmentation"


class TrainerType(str, Enum):
    OTX_1x = "OTX 1.x"
    OTX_2x = "OTX 2.x"


class DatasetIEProjectType(str, Enum):
    """
    Project types supported by Geti in the context of dataset import/export.
    The enum values match the names adopted by the dataset import API
    """

    CLASSIFICATION = "classification"
    CLASSIFICATION_HIERARCHICAL = "classification_hierarchical"
    DETECTION = "detection"
    DETECTION_ORIENTED = "detection_oriented"
    SEGMENTATION = "segmentation"
    INSTANCE_SEGMENTATION = "instance_segmentation"
    ANOMALY = "anomaly"
    KEYPOINT_DETECTION = "keypoint_detection"
    DETECTION_CLASSIFICATION = "detection_classification"
    DETECTION_SEGMENTATION = "detection_segmentation"


# Map project types to the respective task types
PROJECT_TYPE_TO_TASK_MAPPING: dict[ProjectType, list[TaskType]] = {
    ProjectType.MULTICLASS_CLASSIFICATION: [TaskType.CLASSIFICATION],
    ProjectType.MULTILABEL_CLASSIFICATION: [TaskType.CLASSIFICATION],
    ProjectType.HIERARCHICAL_CLASSIFICATION: [TaskType.CLASSIFICATION],
    ProjectType.DETECTION: [TaskType.DETECTION],
    ProjectType.ORIENTED_DETECTION: [TaskType.ROTATED_DETECTION],
    ProjectType.INSTANCE_SEGMENTATION: [TaskType.INSTANCE_SEGMENTATION],
    ProjectType.SEMANTIC_SEGMENTATION: [TaskType.SEGMENTATION],
    ProjectType.ANOMALY_DETECTION: [TaskType.ANOMALY],
    ProjectType.KEYPOINT_DETECTION: [TaskType.KEYPOINT_DETECTION],
    ProjectType.TASK_CHAIN_DETECTION_CLASSIFICATION: [
        TaskType.DETECTION,
        TaskType.CLASSIFICATION,
    ],
    ProjectType.TASK_CHAIN_DETECTION_SEGMENTATION: [
        TaskType.DETECTION,
        TaskType.SEGMENTATION,
    ],
}

# Map project types to the respective empty label name.
# If the project type does not feature an empty label, the value is set to None.
PROJECT_TYPE_TO_EMPTY_LABEL_NAME_MAPPING = {
    ProjectType.MULTICLASS_CLASSIFICATION: None,
    ProjectType.MULTILABEL_CLASSIFICATION: "No class",
    ProjectType.HIERARCHICAL_CLASSIFICATION: None,
    ProjectType.DETECTION: "No object",
    ProjectType.ORIENTED_DETECTION: "No object",
    ProjectType.INSTANCE_SEGMENTATION: "Empty",
    ProjectType.SEMANTIC_SEGMENTATION: "Empty",
    ProjectType.ANOMALY_DETECTION: None,
    ProjectType.KEYPOINT_DETECTION: None,
    ProjectType.TASK_CHAIN_DETECTION_CLASSIFICATION: "No object",
    ProjectType.TASK_CHAIN_DETECTION_SEGMENTATION: "No object",
}


# Map project types to the equivalent dataset import/export project types
PROJECT_TYPE_TO_DATASET_IE_PROJECT_TYPE_MAPPING: dict[ProjectType, DatasetIEProjectType] = {
    ProjectType.MULTICLASS_CLASSIFICATION: DatasetIEProjectType.CLASSIFICATION,
    ProjectType.MULTILABEL_CLASSIFICATION: DatasetIEProjectType.CLASSIFICATION,
    ProjectType.HIERARCHICAL_CLASSIFICATION: DatasetIEProjectType.CLASSIFICATION_HIERARCHICAL,
    ProjectType.DETECTION: DatasetIEProjectType.DETECTION,
    ProjectType.ORIENTED_DETECTION: DatasetIEProjectType.DETECTION_ORIENTED,
    ProjectType.INSTANCE_SEGMENTATION: DatasetIEProjectType.INSTANCE_SEGMENTATION,
    ProjectType.SEMANTIC_SEGMENTATION: DatasetIEProjectType.SEGMENTATION,
    ProjectType.ANOMALY_DETECTION: DatasetIEProjectType.ANOMALY,
    ProjectType.KEYPOINT_DETECTION: DatasetIEProjectType.KEYPOINT_DETECTION,
    ProjectType.TASK_CHAIN_DETECTION_CLASSIFICATION: DatasetIEProjectType.DETECTION_CLASSIFICATION,
    ProjectType.TASK_CHAIN_DETECTION_SEGMENTATION: DatasetIEProjectType.DETECTION_SEGMENTATION,
}
