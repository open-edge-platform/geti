// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Point, Polygon } from '../../../../shared/types';
import { canClosePolygonAt } from './utils';

const triangle: Point[] = [
    { x: 0, y: 0 },
    { x: 100, y: 0 },
    { x: 50, y: 100 },
];
const toPolygon = (points: Point[]): Polygon => ({ type: 'polygon', points });

describe('canClosePolygonAt', () => {
    const radius = 6;
    const nearStart = { x: 2, y: 2 };

    it('returns true when the polygon is valid and the point is over the starting point', () => {
        expect(canClosePolygonAt([triangle], toPolygon(triangle), nearStart, radius)).toBe(true);
    });

    it('returns false when the point is away from the starting point', () => {
        expect(canClosePolygonAt([triangle], toPolygon(triangle), { x: 50, y: 50 }, radius)).toBe(false);
    });

    it('returns false when there are no segments yet', () => {
        expect(canClosePolygonAt([], toPolygon(triangle), nearStart, radius)).toBe(false);
    });

    it('returns false when there is no polygon', () => {
        expect(canClosePolygonAt([triangle], null, nearStart, radius)).toBe(false);
    });

    it('returns false when the polygon is not valid yet', () => {
        const line = triangle.slice(0, 2);

        expect(canClosePolygonAt([line], toPolygon(line), nearStart, radius)).toBe(false);
    });
});
