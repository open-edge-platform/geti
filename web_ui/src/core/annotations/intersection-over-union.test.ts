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

import { intersectionOverUnion } from './intersection-over-union';
import { Rect } from './shapes.interface';

describe('intersection-over-union', () => {
    const rect = { shapeType: 1, x: 0, y: 0, width: 0, height: 0 };
    const testData: [Rect, Rect, number][] = [
        [{ ...rect, x: 0, y: 0, width: 50, height: 50 }, { ...rect, x: 25, y: 25, width: 50, height: 50 }, 0.14],
        [{ ...rect, x: 0, y: 0, width: 50, height: 50 }, { ...rect, x: 25, y: 0, width: 50, height: 50 }, 0.33],
        [{ ...rect, x: 0, y: 0, width: 50, height: 50 }, { ...rect, x: 50, y: 0, width: 50, height: 50 }, 0],
        [{ ...rect, x: 0, y: 0, width: 50, height: 50 }, { ...rect, x: 0, y: 50, width: 50, height: 50 }, 0],
        [{ ...rect, x: 0, y: 0, width: 50, height: 50 }, { ...rect, x: 0, y: 0, width: 50, height: 50 }, 1],
        [{ ...rect, x: 320, y: 435, width: 40, height: 42 }, { ...rect, x: 372, y: 640, width: 37, height: 37 }, 0],
    ];

    test.each(testData)('uses two rects %p %p to calculate iou of %p', (rectA, rectB, expectedValue) => {
        expect(intersectionOverUnion(rectA, rectB)).toBeCloseTo(expectedValue);
    });
});
