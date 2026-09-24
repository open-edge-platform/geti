// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sampleVideoFrameIndexes } from './batch-annotate';

describe('video frame sampling', () => {
    it('starts at the first frame the annotations endpoint can persist', () => {
        expect(sampleVideoFrameIndexes(100, 30)).toEqual([1, 31, 61, 91]);
    });

    it('returns no work for a video containing only frame zero', () => {
        expect(sampleVideoFrameIndexes(1, 30)).toEqual([]);
    });
});
