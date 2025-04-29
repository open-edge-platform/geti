// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
