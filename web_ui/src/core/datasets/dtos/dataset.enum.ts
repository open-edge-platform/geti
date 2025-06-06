// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export enum DATASET_IMPORT_TASK_TYPE_DTO {
    ANOMALY = 'anomaly',
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
