// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
