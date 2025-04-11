// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { WorkspaceIdentifier } from '../workspaces/services/workspaces.interface';

export interface ProjectIdentifier extends WorkspaceIdentifier {
    projectId: string;
}

export enum DOMAIN {
    ANOMALY_CLASSIFICATION = 'Anomaly classification',
    ANOMALY_DETECTION = 'Anomaly detection',
    ANOMALY_SEGMENTATION = 'Anomaly segmentation',
    CLASSIFICATION = 'Classification',
    CROP = 'Crop',
    DETECTION = 'Detection',
    DETECTION_ROTATED_BOUNDING_BOX = 'Detection oriented',
    SEGMENTATION = 'Segmentation',
    SEGMENTATION_INSTANCE = 'Instance segmentation',
    KEYPOINT_DETECTION = 'Keypoint detection',
}
