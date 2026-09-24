// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sampleVideoFrameIndexes, shouldSkipAlreadyAnnotated } from './batch-annotate';

describe('video frame sampling', () => {
    it('starts at the first frame the annotations endpoint can persist', () => {
        expect(sampleVideoFrameIndexes(100, 30)).toEqual([1, 31, 61, 91]);
    });

    it('returns no work for a video containing only frame zero', () => {
        expect(sampleVideoFrameIndexes(1, 30)).toEqual([]);
    });

    it.each([
        [1, 10],
        [2, 20],
        [5, 50],
        [10, 100],
    ] as const)('samples a 10-second 24 FPS video at %s frame(s) per second', (rate, expected) => {
        expect(sampleVideoFrameIndexes(241, 24, rate)).toHaveLength(expected);
    });

    it('never samples faster than the source frame rate', () => {
        expect(sampleVideoFrameIndexes(11, 2, 10)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    });
});

describe('unannotated-only scope', () => {
    it('skips only items that are already annotated', () => {
        expect(shouldSkipAlreadyAnnotated(true, true)).toBe(true);
        expect(shouldSkipAlreadyAnnotated(true, false)).toBe(false);
        expect(shouldSkipAlreadyAnnotated(false, true)).toBe(false);
    });
});
