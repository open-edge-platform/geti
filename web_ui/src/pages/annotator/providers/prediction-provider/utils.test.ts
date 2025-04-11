// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import sortBy from 'lodash/sortBy';

import { labelFromModel } from '../../../../core/annotations/utils';
import { hasDifferentId, hasEqualId } from '../../../../shared/utils';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { minimalThresholdPercentage, selectFirstOrNoneFromList, sortExplanationsByName } from './utils';

const roi = {
    id: 'roi-id',
    shape: {
        y: 0,
        x: 0,
        type: 'rectangle',
        height: 10,
        width: 10,
    },
};
const mockedExplanation = {
    labelsId: '123',
    id: '321',
    url: 'url-test',
    name: 'name-test',
    roi,
};

const mockedExplanation2 = {
    labelsId: '1234',
    id: '3214',
    url: 'url-test4',
    name: 'name-test4',
    roi,
};

jest.mock('lodash/sortBy');

describe('prediction-provider utils', () => {
    it('hasEqualId', () => {
        expect(hasEqualId('123')({ id: '123' })).toBe(true);
        expect(hasEqualId('123')({ id: '321' })).toBe(false);
    });

    it('hasDifferentId', () => {
        expect(hasDifferentId('123')({ id: '321' })).toBe(true);
        expect(hasDifferentId('123')({ id: '123' })).toBe(false);
    });

    describe('minimalThresholdPercentage', () => {
        it('only predictions', () => {
            const emptyScore = { ...labelFromModel(getMockedLabel({}), 0, '123', '321'), score: undefined };
            const mockAnnotations = [
                getMockedAnnotation({
                    labels: [labelFromModel(getMockedLabel({}), 0.5, '123', '321')],
                }),
                getMockedAnnotation({
                    labels: [labelFromModel(getMockedLabel({}), 0.8, '123', '321')],
                }),
            ];

            expect(minimalThresholdPercentage(mockAnnotations)).toBe(50);
            expect(minimalThresholdPercentage([getMockedAnnotation({ labels: [emptyScore] })])).toBe(100);
        });

        it('prediction and annotations', () => {
            const mockAnnotations = [
                getMockedAnnotation({
                    labels: [labelFromModel(getMockedLabel({ name: 'label1' }), 0.5, '123', '321')],
                }),
                getMockedAnnotation({}),
                getMockedAnnotation({
                    labels: [labelFromModel(getMockedLabel({ name: 'label3' }), 0.2, '123', '321')],
                }),
                getMockedAnnotation({}),
            ];
            expect(minimalThresholdPercentage(mockAnnotations)).toBe(20);
        });

        it('only annotations', () => {
            const mockAnnotations = [getMockedAnnotation({}), getMockedAnnotation({})];
            expect(minimalThresholdPercentage(mockAnnotations)).toBe(0);
        });
    });

    it('selectFirstOrNoneFromList', () => {
        expect(selectFirstOrNoneFromList([])).toEqual(undefined);
        expect(selectFirstOrNoneFromList([mockedExplanation])).toEqual(mockedExplanation);
        expect(selectFirstOrNoneFromList([mockedExplanation, mockedExplanation2])).toEqual(mockedExplanation);
    });

    it('sortExplanationsByName', () => {
        sortExplanationsByName([mockedExplanation]);

        const [firstCall] = jest.mocked(sortBy).mock.calls;
        const callback = firstCall[1] as (data: unknown) => string;
        expect(callback(mockedExplanation)).toBe(mockedExplanation.name);
        expect(sortBy).toHaveBeenCalledWith([mockedExplanation], expect.any(Function));
    });
});
