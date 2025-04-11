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
