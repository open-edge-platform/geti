// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { RegionOfInterest } from '../../../core/annotations/annotation.interface';
import { BoundingBox } from '../../../core/annotations/math';
import { Circle, Point, Rect } from '../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { getMockedAnnotation } from '../../../test-utils/mocked-items-factory/mocked-annotations';
import {
    isInsideBoundingBox,
    isPointWithinRoi,
    isRectWithinRoi,
    isShapeWithinRoi,
    removeOffLimitPointsPolygon,
    transformToClipperShape,
} from './utils';

describe('annotator utils', () => {
    describe('removeOffLimitPoints', () => {
        const roi: RegionOfInterest = {
            x: 0,
            y: 0,
            width: 100,
            height: 100,
        };
        const getRect = (x: number, y: number): Rect => ({
            x,
            y,
            width: roi.width,
            height: roi.height,
            shapeType: ShapeType.Rect,
        });

        test.each([
            [
                'top',
                getRect(roi.x, -roi.height / 2),
                [
                    { x: 100, y: 50 },
                    { x: 0, y: 50 },
                    { x: 0, y: 0 },
                    { x: 100, y: 0 },
                ],
            ],
            [
                'left/top corner',
                getRect(-roi.width / 2, -roi.height / 2),
                [
                    { x: 50, y: 50 },
                    { x: 0, y: 50 },
                    { x: 0, y: 0 },
                    { x: 50, y: 0 },
                ],
            ],
            [
                'left',
                getRect(-roi.width / 2, roi.y),
                [
                    { x: 50, y: 100 },
                    { x: 0, y: 100 },
                    { x: 0, y: 0 },
                    { x: 50, y: 0 },
                ],
            ],
            [
                'left/bottom corner',
                getRect(-roi.width / 2, roi.height / 2),
                [
                    { x: 50, y: 100 },
                    { x: 0, y: 100 },
                    { x: 0, y: 50 },
                    { x: 50, y: 50 },
                ],
            ],
            [
                'bottom',
                getRect(roi.x, roi.height / 2),
                [
                    { x: 100, y: 100 },
                    { x: 0, y: 100 },
                    { x: 0, y: 50 },
                    { x: 100, y: 50 },
                ],
            ],
            [
                'right/bottom corner',
                getRect(roi.width / 2, roi.height / 2),
                [
                    { x: 100, y: 100 },
                    { x: 50, y: 100 },
                    { x: 50, y: 50 },
                    { x: 100, y: 50 },
                ],
            ],
            [
                'right',
                getRect(roi.width / 2, roi.y),
                [
                    { x: 100, y: 100 },
                    { x: 50, y: 100 },
                    { x: 50, y: 0 },
                    { x: 100, y: 0 },
                ],
            ],
            [
                'right/top corner',
                getRect(roi.width / 2, -roi.height / 2),
                [
                    { x: 100, y: 50 },
                    { x: 50, y: 50 },
                    { x: 50, y: 0 },
                    { x: 100, y: 0 },
                ],
            ],
        ])('remove offlimit %o', (_, outlineShape: Rect, result): void => {
            const newShape = removeOffLimitPointsPolygon(outlineShape, roi);

            expect(newShape.points).toEqual(
                expect.arrayContaining([
                    expect.objectContaining(result[0]),
                    expect.objectContaining(result[1]),
                    expect.objectContaining(result[2]),
                    expect.objectContaining(result[3]),
                ])
            );

            const rioRect: Rect = { ...roi, shapeType: ShapeType.Rect };
            expect(transformToClipperShape(rioRect).totalArea()).toBeGreaterThan(
                transformToClipperShape(newShape).totalArea()
            );
            expect(newShape.shapeType).toBe(ShapeType.Polygon);
        });
    });

    describe('isPointWithinRoi', () => {
        const boundingBox = { x: 0, y: 0, width: 200, height: 100 };
        const testData: [Point, boolean][] = [
            [{ x: 25, y: 25 }, true],
            [{ x: -25, y: 25 }, false],
            [{ x: -25, y: -25 }, false],
            [{ x: 200, y: 100 }, true],
            [{ x: 201, y: 100 }, false],
            [{ x: 200, y: 101 }, false],
        ];
        test.each(testData)('test if point %s is inside of roi (%s)', (point, expectedResult) => {
            expect(isPointWithinRoi(boundingBox, point)).toEqual(expectedResult);
        });
    });

    describe('isShapeWithinRoi', () => {
        const roi = { x: 0, y: 0, width: 100, height: 100 };

        it('inside', () => {
            const circle: Circle = { x: 10, y: 10, r: 20, shapeType: ShapeType.Circle };
            expect(isShapeWithinRoi(roi, circle)).toBe(true);
        });

        it('partially inside', () => {
            const circle: Circle = { x: -19, y: 0, r: 20, shapeType: ShapeType.Circle };
            expect(isShapeWithinRoi(roi, circle)).toBe(true);
        });

        it('outside', () => {
            const circle: Circle = { x: -20, y: 0, r: 20, shapeType: ShapeType.Circle };
            expect(isShapeWithinRoi(roi, circle)).toBe(false);
        });
    });

    describe('isRectWithinRoi', () => {
        const roi = { x: 0, y: 0, width: 50, height: 50 };
        const rect: Rect = { ...roi, shapeType: ShapeType.Rect };

        it('inside', () => {
            expect(isRectWithinRoi(roi, rect)).toBe(true);
        });

        it('negative X', () => {
            expect(isRectWithinRoi(roi, { ...rect, x: -1 })).toBe(false);
        });

        it('invalid X', () => {
            expect(isRectWithinRoi(roi, { ...rect, x: roi.width + 1 })).toBe(false);
        });

        it('invalid With', () => {
            expect(isRectWithinRoi(roi, { ...rect, width: roi.width + 10 })).toBe(false);
        });

        it('negative Y', () => {
            expect(isRectWithinRoi(roi, { ...rect, y: -1 })).toBe(false);
        });

        it('invalid Y', () => {
            expect(isRectWithinRoi(roi, { ...rect, y: roi.height + 1 })).toBe(false);
        });

        it('invalid height', () => {
            expect(isRectWithinRoi(roi, { ...rect, height: roi.height + 10 })).toBe(false);
        });

        it('complex roi', () => {
            const complexRoi = { x: 2042, y: 1888, width: 1315, height: 854 };
            expect(
                isRectWithinRoi(complexRoi, {
                    ...rect,
                    x: 2803,
                    y: 2209,
                    width: 224,
                    height: 167,
                })
            ).toBe(true);
        });
    });

    describe('isInsideBoundingBox', () => {
        const boundingBox: BoundingBox = {
            x: 0,
            y: 0,
            width: 100,
            height: 100,
        };

        describe('At least some part of the circle should be inside of the ROI(boundingBox)', () => {
            it('inside', () => {
                const circle = getMockedAnnotation(
                    { shape: { shapeType: ShapeType.Circle, x: 50, y: 50, r: 30 } },
                    ShapeType.Circle
                );
                expect(isInsideBoundingBox(circle)(boundingBox)).toBe(true);
            });

            it('partially inside', () => {
                const circle = getMockedAnnotation(
                    { shape: { shapeType: ShapeType.Circle, x: -29, y: 10, r: 30 } },
                    ShapeType.Circle
                );
                expect(isInsideBoundingBox(circle)(boundingBox)).toBe(true);
            });

            it('outinside', () => {
                const circle = getMockedAnnotation(
                    { shape: { shapeType: ShapeType.Circle, x: -32, y: 10, r: 30 } },
                    ShapeType.Circle
                );
                expect(isInsideBoundingBox(circle)(boundingBox)).toBe(false);
            });
        });
    });
});
