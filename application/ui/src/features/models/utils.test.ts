// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { distributeByLargestRemainder } from './utils';

describe('distributeByLargestRemainder', () => {
    it('returns all zeros when total is zero', () => {
        expect(distributeByLargestRemainder([70, 20, 10], 0)).toEqual([0, 0, 0]);
    });

    it('returns all zeros when sum of values is zero', () => {
        expect(distributeByLargestRemainder([0, 0, 0], 100)).toEqual([0, 0, 0]);
    });

    it('returns empty array for empty input with non-zero total', () => {
        expect(distributeByLargestRemainder([], 100)).toEqual([]);
    });

    it('result always sums to total', () => {
        const result = distributeByLargestRemainder([750, 125, 125], 100);
        expect(result.reduce((a, b) => a + b, 0)).toBe(100);
        expect(result).toEqual([75, 13, 12]);
    });

    it('tie-breaking: largest fractional part gets the extra unit', () => {
        // [1, 1, 1] → each gets 33.33%, floors to 33, remainder = 1
        // all fractionals equal → first in sorted order wins
        const result = distributeByLargestRemainder([1, 1, 1], 100);
        expect(result.reduce((a, b) => a + b, 0)).toBe(100);
        expect(result).toEqual([34, 33, 33]);
    });

    it('count case: 45/28/27 split on 5 items → [2, 2, 1]', () => {
        expect(distributeByLargestRemainder([45, 28, 27], 5)).toEqual([2, 2, 1]);
    });

    it('standard percentage case: 70/20/10 on 100 → [70, 20, 10]', () => {
        expect(distributeByLargestRemainder([70, 20, 10], 100)).toEqual([70, 20, 10]);
    });

    it('handles a single value', () => {
        expect(distributeByLargestRemainder([5], 100)).toEqual([100]);
    });
});
