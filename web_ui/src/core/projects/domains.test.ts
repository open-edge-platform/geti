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
import { isAnomalyDomain, isClassificationDomain, isDetectionDomain, isSegmentationDomain } from './domains';

describe('domains', () => {
    it.each([
        [DOMAIN.CLASSIFICATION, true],
        [DOMAIN.ANOMALY_CLASSIFICATION, true],
        [DOMAIN.DETECTION, false],
        [DOMAIN.ANOMALY_DETECTION, false],
        [DOMAIN.SEGMENTATION, false],
        [DOMAIN.ANOMALY_SEGMENTATION, false],
    ])('isClassificationDomain(%o) is %o', (domain, result) => {
        expect(isClassificationDomain(domain)).toBe(result);
    });

    it.each([
        [DOMAIN.CLASSIFICATION, false],
        [DOMAIN.ANOMALY_CLASSIFICATION, false],
        [DOMAIN.DETECTION, true],
        [DOMAIN.ANOMALY_DETECTION, true],
        [DOMAIN.SEGMENTATION, false],
        [DOMAIN.ANOMALY_SEGMENTATION, false],
    ])('isDetectionDomain(%o) is %o', (domain, result) => {
        expect(isDetectionDomain(domain)).toBe(result);
    });

    it.each([
        [DOMAIN.CLASSIFICATION, false],
        [DOMAIN.ANOMALY_CLASSIFICATION, false],
        [DOMAIN.DETECTION, false],
        [DOMAIN.ANOMALY_DETECTION, false],
        [DOMAIN.SEGMENTATION, true],
        [DOMAIN.ANOMALY_SEGMENTATION, true],
    ])('isSegmentationDomain(%o) is %o', (domain, result) => {
        expect(isSegmentationDomain(domain)).toBe(result);
    });

    it.each([
        [DOMAIN.CLASSIFICATION, false],
        [DOMAIN.ANOMALY_CLASSIFICATION, true],
        [DOMAIN.DETECTION, false],
        [DOMAIN.ANOMALY_DETECTION, true],
        [DOMAIN.SEGMENTATION, false],
        [DOMAIN.ANOMALY_SEGMENTATION, true],
    ])('isAnomalyDomain(%o) is %o', (domain, result) => {
        expect(isAnomalyDomain(domain)).toBe(result);
    });
});
