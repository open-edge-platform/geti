// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { labelFromModel } from '../../../core/annotations/utils';
import { getMockedAnnotation } from '../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { getPredictionAnnotations, isPredictionAnnotation } from '../utils';
import { formatPerformanceScore } from './utils';

describe('Annotator components utils', () => {
    const userAnnotation = getMockedAnnotation({ id: 'test-annotation-3' });
    const suggestedAnnotation = getMockedAnnotation({
        id: 'test-annotation-3',
        labels: [labelFromModel(getMockedLabel({}), 1, '123', '321')],
    });

    it('isPredictionAnnotation', () => {
        expect(isPredictionAnnotation(userAnnotation)).toBe(false);
        expect(isPredictionAnnotation(suggestedAnnotation)).toBe(true);
    });

    it('getPredictionAnnotations', () => {
        expect(getPredictionAnnotations([userAnnotation, suggestedAnnotation])).toEqual([suggestedAnnotation]);
    });

    it('formatPerformanceScore', () => {
        expect(formatPerformanceScore(null)).toEqual('N/A');
        expect(formatPerformanceScore(0.15)).toEqual('15%');
    });
});
