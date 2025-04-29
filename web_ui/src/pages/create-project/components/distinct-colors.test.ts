// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getDistinctColorBasedOnHash, getHEXFormat } from './distinct-colors';

describe('Distinct colors', () => {
    it('getHEXFormat - get color format from hex with alpha - should return hex', () => {
        expect(getHEXFormat('#6611ddff')).toBe('#6611dd');
    });
    it('getHEXFormat - get color format from hex - should return the same', () => {
        expect(getHEXFormat('#6622df')).toBe('#6622df');
    });
});

describe('getDistinctColorBasedOnHash', () => {
    it.each([
        ['#80E9AF', 'validation'],
        ['#E96115', 'test'],
        ['#81407B', 'Size of Test set'],
        ['#CC94DA', 'Size of Validation set'],
        ['#00A5CF', 'Size of Training set'],
    ])('getDistinctColorBasedOnHash(%s) === %s', (expected: string, value: string) => {
        expect(getDistinctColorBasedOnHash(value)).toBe(expected);
    });
});
