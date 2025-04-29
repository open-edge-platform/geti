// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
