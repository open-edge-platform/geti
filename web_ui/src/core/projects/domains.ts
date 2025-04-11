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
