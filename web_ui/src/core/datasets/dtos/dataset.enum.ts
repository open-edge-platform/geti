// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.
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
}
