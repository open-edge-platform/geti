// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum DATASET_IMPORT_WARNING_TYPE {
    WARNING = 'warning',
    ERROR = 'error',
}

export enum DATASET_IMPORT_DIALOG_BUTTONS {
    CANCEL = 'cancel',
    DELETE = 'delete',
    HIDE = 'hide',
    BACK = 'back',
    NEXT = 'next',
    CREATE = 'create',
    IMPORT = 'import',
}

export enum DATASET_IMPORT_STATUSES {
    // Common statuses
    UPLOADING = 'uploading',
    IMPORTING_ERROR = 'importingError',
    IMPORTING_INTERRUPTED = 'importingInterrupted',

    PREPARING = 'preparing',
    PREPARING_ERROR = 'preparingError',

    READY = 'ready',

    // Import to new project statuses
    TASK_TYPE_SELECTION_TO_NEW_PROJECT = 'taskTypeSelectionToNewProject',
    LABELS_SELECTION_TO_NEW_PROJECT = 'labelsSelectionToNewProject',
    IMPORTING_TO_NEW_PROJECT = 'importingToNewProject',
    IMPORTING_TO_NEW_PROJECT_ERROR = 'importingToNewProjectError',

    // Import to existing project statuses
    LABELS_MAPPING_TO_EXISTING_PROJECT = 'labelsMappingToExistingProject',
    IMPORTING_TO_EXISTING_PROJECT = 'importingToExistingProject',
    IMPORTING_TO_EXISTING_PROJECT_ERROR = 'importingToExistingProjectError',
}

export enum DATASET_IMPORT_TO_NEW_PROJECT_STEP {
    DATASET = 'dataset',
    DOMAIN = 'domain',
    LABELS = 'labels',
}

export enum DATASET_IMPORT_TASK_TYPE {
    ANOMALY_CLASSIFICATION = 'anomaly_classification',
    ANOMALY_DETECTION = 'anomaly_detection',
    ANOMALY_SEGMENTATION = 'anomaly_segmentation',
    CLASSIFICATION = 'classification',
    CROP = 'crop',
    DETECTION = 'detection',
    DETECTION_ROTATED_BOUNDING_BOX = 'detection_oriented',
    SEGMENTATION = 'segmentation',
    SEGMENTATION_INSTANCE = 'instance_segmentation',
    DATASET = 'dataset',
    CLASSIFICATION_HIERARCHICAL = 'classification_hierarchical',
    DETECTION_CLASSIFICATION = 'detection_classification',
    DETECTION_SEGMENTATION = 'detection_segmentation',
    KEYPOINT_DETECTION = 'keypoint_detection',
}

export enum DATASET_IMPORT_DOMAIN {
    ANOMALY_CLASSIFICATION = 'Anomaly classification',
    ANOMALY_DETECTION = 'Anomaly detection',
    ANOMALY_SEGMENTATION = 'Anomaly segmentation',
    CLASSIFICATION = 'Classification',
    CROP = 'Crop',
    DETECTION = 'Detection',
    DETECTION_ROTATED_BOUNDING_BOX = 'Detection oriented',
    SEGMENTATION = 'Segmentation',
    SEGMENTATION_INSTANCE = 'Instance segmentation',
    CLASSIFICATION_HIERARCHICAL = 'Classification hierarchical',
    DETECTION_CLASSIFICATION = 'Detection > Classification',
    DETECTION_SEGMENTATION = 'Detection > Segmentation',
    KEYPOINT_DETECTION = 'Keypoint detection',
}
