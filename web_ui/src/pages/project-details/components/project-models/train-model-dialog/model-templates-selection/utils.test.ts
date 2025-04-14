// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { LifecycleStage } from '../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { isDeprecatedAlgorithm, isObsoleteAlgorithm } from './utils';

describe('filterDeprecatedAlgorithm', () => {
    it('should return true for non-deprecated algorithms', () => {
        expect(isDeprecatedAlgorithm(LifecycleStage.ACTIVE)).toBe(false);
    });

    it('should return false for deprecated algorithms', () => {
        expect(isDeprecatedAlgorithm(LifecycleStage.DEPRECATED)).toBe(true);
    });
});

describe('filterObsoleteAlgorithm', () => {
    it('should return true for non-obsolete algorithms', () => {
        expect(isObsoleteAlgorithm(LifecycleStage.ACTIVE)).toBe(false);
    });

    it('should return false for obsolete algorithms', () => {
        expect(isObsoleteAlgorithm(LifecycleStage.OBSOLETE)).toBe(true);
    });
});
