// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { areAllLabelsIncluded, getDuplicates, hasDuplicatedValues } from './utils';

describe('dataset import to existing project utils', () => {
    describe('hasDuplicatedValues', () => {
        it('return false when there are no duplicate values', () => {
            const data = { key1: 'value1', key2: 'value2', key3: 'value3' };
            expect(hasDuplicatedValues(data)).toBe(false);
        });

        it('return true when there are duplicate values', () => {
            const data = { key1: 'value1', key2: 'value1', key3: 'value3' };
            expect(hasDuplicatedValues(data)).toBe(true);
        });
    });

    describe('getDuplicates', () => {
        it('return empty array when there are no duplicate values', () => {
            const items = ['apple', 'banana', 'orange'];
            expect(getDuplicates(items)).toEqual([]);
        });

        it('return an array of duplicate values', () => {
            const items = ['apple', 'banana', 'apple', 'orange', 'banana'];
            expect(getDuplicates(items)).toEqual(['apple', 'banana']);
        });

        it('correctly identify duplicates when there are multiple occurrences', () => {
            const items = ['apple', 'apple', 'apple', 'banana', 'orange'];
            expect(getDuplicates(items)).toEqual(['apple']);
        });
    });

    describe('areAllLabelsIncluded', () => {
        const labels = [
            getMockedLabel({ id: 'label1', name: 'Label 1' }),
            getMockedLabel({ id: 'label2', name: 'Label 2' }),
            getMockedLabel({ id: 'label3', name: 'Label 3' }),
        ];

        it('returns true if some labels are not included in the map values', () => {
            const labelsMap = { source1: 'label1', source2: 'label2' };
            expect(areAllLabelsIncluded(labels, labelsMap)).toBe(true);
        });

        it('returns false if all labels are included in the map values', () => {
            const labelsMap = { source1: 'label1', source2: 'label2', source3: 'label3' };
            expect(areAllLabelsIncluded(labels, labelsMap)).toBe(false);
        });

        it('returns false for empty labels array', () => {
            expect(areAllLabelsIncluded([], { source1: 'label1' })).toBe(false);
        });
    });
});
