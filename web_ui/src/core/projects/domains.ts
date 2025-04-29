// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from './core.interface';

export const DETECTION_DOMAINS = [DOMAIN.DETECTION, DOMAIN.ANOMALY_DETECTION];

export const SEGMENTATION_DOMAINS = [DOMAIN.SEGMENTATION, DOMAIN.SEGMENTATION_INSTANCE, DOMAIN.ANOMALY_SEGMENTATION];

const ANOMALY_DOMAINS = [DOMAIN.ANOMALY_CLASSIFICATION, DOMAIN.ANOMALY_DETECTION, DOMAIN.ANOMALY_SEGMENTATION];

export const isClassificationDomain = (domain: DOMAIN): boolean => {
    return [DOMAIN.CLASSIFICATION, DOMAIN.ANOMALY_CLASSIFICATION].includes(domain);
};

export const isDetectionDomain = (domain: DOMAIN): boolean => {
    return DETECTION_DOMAINS.includes(domain);
};

export const isSegmentationDomain = (domain: DOMAIN): boolean => {
    return SEGMENTATION_DOMAINS.includes(domain);
};

export const isAnomalyDomain = (domain: DOMAIN): boolean => {
    return ANOMALY_DOMAINS.includes(domain);
};

export const isRotatedDetectionDomain = (domain: DOMAIN): boolean => {
    return [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX].includes(domain);
};

export const isKeypointDetection = (domain: DOMAIN): boolean => {
    return [DOMAIN.KEYPOINT_DETECTION].includes(domain);
};
