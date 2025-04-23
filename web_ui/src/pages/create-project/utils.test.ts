// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { EMPTY_LABEL_MESSAGE, getDuplicateLabelNames, getLabelsNamesErrors, MIN_POINTS_MESSAGE } from './utils';

describe('create-project utils', () => {
    describe('getDuplicateLabelNames', () => {
        it('return an empty array if there are no duplicate labels', () => {
            expect(getDuplicateLabelNames(['label A', 'label B'])).toEqual([]);
        });

        it('return an array with duplicate label names', () => {
            expect(getDuplicateLabelNames(['label A', 'label A'])).toEqual(['label A']);
        });

        it('return an array with multiple duplicate label names', () => {
            expect(getDuplicateLabelNames(['label A', 'label B', 'label A', 'label B'])).toEqual([
                'label A',
                'label B',
            ]);
        });
    });

    describe('getLabelsNamesErrors', () => {
        const pointA = 'label A';
        const pointB = 'label B';
        const pointC = 'label A';
        const pointD = '';
        const pointF = '';

        it('returns MIN_POINTS_MESSAGE if no points are provided', () => {
            expect(getLabelsNamesErrors([])).toBe(MIN_POINTS_MESSAGE);
        });

        it('returns EMPTY_LABEL_MESSAGE if there are empty labels', () => {
            expect(getLabelsNamesErrors([pointA, pointD])).toBe(EMPTY_LABEL_MESSAGE);
            expect(getLabelsNamesErrors([pointC, pointF])).toBe(EMPTY_LABEL_MESSAGE);
        });

        it('returns an error message if there are duplicate labels', () => {
            expect(getLabelsNamesErrors([pointA, pointC])).toBe(
                'Label names must be unique, label "label A" is duplicated'
            );
        });

        it('returns an error message if there are multiple duplicate labels', () => {
            const pointE = 'label B';
            expect(getLabelsNamesErrors([pointA, pointB, pointC, pointE])).toBe(
                'Label names must be unique, labels "label A" ,"label B" are duplicated'
            );
        });

        it('returns undefined if there are no duplicate labels and no empty labels', () => {
            expect(getLabelsNamesErrors([pointA, pointB])).toBeUndefined();
        });
    });
});
