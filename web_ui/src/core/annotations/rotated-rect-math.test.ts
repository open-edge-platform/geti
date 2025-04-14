// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { highestCorner } from './math';
import {
    calculateSizeAndPositionBasedOfCornerAnchor,
    calculateSizeAndPositionOfSideAnchor,
    cursorForDirection,
    rectToRotatedRect,
    transformPointInRotatedRectToScreenSpace,
} from './rotated-rect-math';
import { Rect, RotatedRect } from './shapes.interface';
import { ShapeType } from './shapetype.enum';
import * as Vec2 from './vec2';

describe('transformPointInRotatedRectToScreenSpace', () => {
    const shape: RotatedRect = {
        x: 100,
        y: 100,
        width: 100,
        height: 100,
        angle: 90,
        shapeType: ShapeType.RotatedRect,
    };

    it('does not change position of center', () => {
        const position = { x: 100, y: 100 };
        const result = transformPointInRotatedRectToScreenSpace(position, shape);
        expect(result).toEqual({ x: 100, y: 100 });
    });

    it('transforms a position in rotated rect space to screen space', () => {
        const position = { x: 50, y: 50 };
        const result = transformPointInRotatedRectToScreenSpace(position, shape);
        expect(result).toEqual({ x: 150, y: 50 });
    });
});

describe('calculateSizeAndPositionBasedOnCornerAnchor', () => {
    const shape: RotatedRect = {
        x: 100,
        y: 100,
        width: 100,
        height: 100,
        angle: 0,
        shapeType: ShapeType.RotatedRect,
    };

    const gap = 10;

    it('moves north west corner 10px diagonally in', () => {
        const cornerNW = { x: 50, y: 50 };
        const cornerSE = { x: 150, y: 150 };
        const position = { x: 60, y: 60 };
        const result = calculateSizeAndPositionBasedOfCornerAnchor(position, cornerNW, cornerSE, shape, gap);
        expect(result).toEqual({ x: 105, y: 105, width: 90, height: 90 });
    });

    it('moves north west corner 10px downwards', () => {
        const cornerNW = { x: 50, y: 50 };
        const cornerSE = { x: 150, y: 150 };
        const position = { x: 50, y: 60 };
        const result = calculateSizeAndPositionBasedOfCornerAnchor(position, cornerNW, cornerSE, shape, gap);
        expect(result).toEqual({ x: 100, y: 105, width: 100, height: 90 });
    });

    it('moves south west corner 10px up', () => {
        const cornerNE = { x: 150, y: 50 };
        const cornerSW = { x: 50, y: 150 };
        const position = { x: 50, y: 140 };
        const result = calculateSizeAndPositionBasedOfCornerAnchor(position, cornerSW, cornerNE, shape, gap);
        expect(result).toEqual({ x: 100, y: 95, width: 100, height: 90 });
    });

    it('will not be smaller than the gap', () => {
        const cornerNE = { x: 150, y: 50 };
        const cornerSW = { x: 50, y: 150 };
        const position = { x: 149, y: 51 };
        const result = calculateSizeAndPositionBasedOfCornerAnchor(position, cornerSW, cornerNE, shape, gap);
        expect(result).toEqual({ x: 145, y: 55, width: gap, height: gap });
    });
});

describe('calculatePositionAndSizeOfSideAnchor', () => {
    type Input = [Vec2.Vec2, Vec2.Vec2, Vec2.Vec2, number];
    type Result = { x: number; y: number; size: number };

    const testInputs: [Input, Result][] = [
        [[{ x: 50, y: 50 }, { x: 0, y: 50 }, { x: 100, y: 50 }, 10], { x: 75, y: 50, size: 50 }], // move W right
        [[{ x: 50, y: 50 }, { x: 100, y: 50 }, { x: 0, y: 50 }, 10], { x: 25, y: 50, size: 50 }], // move E left
        [[{ x: 50, y: 50 }, { x: 50, y: 100 }, { x: 50, y: 0 }, 10], { x: 50, y: 25, size: 50 }], // move S up
        [[{ x: 50, y: 50 }, { x: 50, y: 0 }, { x: 50, y: 100 }, 10], { x: 50, y: 75, size: 50 }], // move N down
        [[{ x: -50, y: 50 }, { x: 0, y: 50 }, { x: 100, y: 50 }, 10], { x: 25, y: 50, size: 150 }], // move W left
        [[{ x: 150, y: 50 }, { x: 100, y: 50 }, { x: 0, y: 50 }, 10], { x: 75, y: 50, size: 150 }], // move E right
        [[{ x: 50, y: 150 }, { x: 50, y: 100 }, { x: 50, y: 0 }, 10], { x: 50, y: 75, size: 150 }], // move S down
        [[{ x: 50, y: -50 }, { x: 50, y: 0 }, { x: 50, y: 100 }, 10], { x: 50, y: 25, size: 150 }], // move N up
    ];
    test.each(testInputs)(
        'calculates new position and size',
        ([pos, c1, c2, gap]: Input, expectedResult: Result): void => {
            expect(calculateSizeAndPositionOfSideAnchor(pos, c1, c2, gap)).toEqual(expectedResult);
        }
    );
});

describe('highestCorner', () => {
    const baseShape: RotatedRect = {
        x: 100,
        y: 100,
        width: 100,
        height: 100,
        angle: 0,
        shapeType: ShapeType.RotatedRect,
    };

    const testInputs: [number, Vec2.Vec2][] = [
        [0, { x: 50, y: 50 }],
        [45, { x: 100, y: 29.29 }],
        [135, { x: 100, y: 29.29 }],
    ];

    test.each(testInputs)(
        'calculates the highest corner of a rotated rectangle angle %p to be %p',
        (angle: number, expectedResult: Vec2.Vec2): void => {
            const result = highestCorner({ ...baseShape, angle });
            expect(result.x).toBeCloseTo(expectedResult.x);
            expect(result.y).toBeCloseTo(expectedResult.y);
        }
    );
});

describe('cursorForDirection', () => {
    const testInputs: [Vec2.Vec2, string][] = [
        [{ x: 100, y: 0 }, 'e-resize'],
        [{ x: 100, y: 100 }, 'se-resize'],
        [{ x: 0, y: 100 }, 's-resize'],
        [{ x: -100, y: 100 }, 'sw-resize'],
        [{ x: -100, y: 0 }, 'w-resize'],
        [{ x: -100, y: -100 }, 'nw-resize'],
        [{ x: 0, y: -100 }, 'n-resize'],
        [{ x: 100, y: -100 }, 'ne-resize'],
        [{ x: 60, y: -100 }, 'ne-resize'],
        [{ x: 40, y: -100 }, 'n-resize'],
    ];

    test.each(testInputs)('uses direction %p to calculate the cursor name %p', (input, expectedResult) => {
        expect(cursorForDirection(input, { x: 0, y: 0 })).toEqual(expectedResult);
    });
});

describe('rectToRotatedRect', () => {
    test('transforms rect to rotatedRect', () => {
        const rect: Rect = {
            shapeType: ShapeType.Rect,
            x: 50,
            y: 80,
            width: 40,
            height: 30,
        };
        expect(rectToRotatedRect(rect)).toEqual({
            shapeType: ShapeType.RotatedRect,
            x: 70,
            y: 95,
            width: 40,
            height: 30,
            angle: 0,
        });
    });
});
