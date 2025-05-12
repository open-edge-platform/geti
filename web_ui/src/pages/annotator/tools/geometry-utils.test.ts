// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Feature, MultiPolygon } from 'geojson';

import { RegionOfInterest } from '../../../core/annotations/annotation.interface';
import { Circle, Point, Polygon, Rect, RotatedRect } from '../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import {
    calculateCirclePoints,
    calculatePolygonArea,
    calculateRectanglePoints,
    calculateRotatedRectanglePoints,
    findLargestPolygon,
    getShapesUnion,
    isPointWithinRoi,
    isPolygonValid,
    isShapePartiallyWithinROI,
    isShapeWithinRoi,
    removeOffLimitPointsPolygon,
    shapeToTurfPolygon,
    TurfPolygon,
} from './geometry-utils';

describe('geometry-utils', () => {
    describe('calculateRectanglePoints', () => {
        it('should calculate rectangle points correctly', () => {
            const rect = { x: 0, y: 0, width: 10, height: 5 };
            const points = calculateRectanglePoints(rect);
            expect(points).toEqual([
                [0, 0],
                [10, 0],
                [10, 5],
                [0, 5],
            ]);
        });

        it('should handle rectangles with zero width or height', () => {
            const rect = { x: 0, y: 0, width: 0, height: 5 };
            const points = calculateRectanglePoints(rect);

            expect(points).toEqual([
                [0, 0],
                [0, 0],
                [0, 5],
                [0, 5],
            ]);
        });
    });

    describe('calculateRotatedRectanglePoints', () => {
        it('should calculate rotated rectangle points correctly', () => {
            const rotatedRect: RotatedRect = {
                shapeType: ShapeType.RotatedRect,
                x: 0,
                y: 0,
                width: 10,
                height: 5,
                angle: 45,
            };
            const points = calculateRotatedRectanglePoints(rotatedRect);

            expect(points).toHaveLength(4);
        });

        it('should handle rectangles with zero rotation', () => {
            const rotatedRect: RotatedRect = {
                shapeType: ShapeType.RotatedRect,
                x: 0,
                y: 0,
                width: 10,
                height: 5,
                angle: 0,
            };
            const points = calculateRotatedRectanglePoints(rotatedRect);

            expect(points).toHaveLength(4);
        });
    });

    describe('shapeToTurfPolygon', () => {
        it('should convert a rectangle to a Turf polygon', () => {
            const rect: Rect = { x: 0, y: 0, width: 10, height: 5, shapeType: ShapeType.Rect };
            const turfPolygon = shapeToTurfPolygon(rect);

            expect(turfPolygon.geometry.coordinates[0]).toHaveLength(5); // Closed polygon
        });

        it('should handle invalid shapes gracefully', () => {
            const invalidShape = { x: 0, y: 0, shapeType: 'InvalidType' } as never;

            expect(() => shapeToTurfPolygon(invalidShape)).toThrow();
        });
    });

    describe('isPolygonValid', () => {
        it('should validate a polygon with sufficient area', () => {
            const polygonShape: Polygon = {
                shapeType: ShapeType.Polygon,
                points: [
                    { x: 0, y: 0 },
                    { x: 10, y: 0 },
                    { x: 10, y: 10 },
                    { x: 0, y: 10 },
                ],
            };
            expect(isPolygonValid(polygonShape)).toBe(true);
        });

        it('should invalidate a polygon with insufficient area', () => {
            const polygonShape: Polygon = {
                shapeType: ShapeType.Polygon,
                points: [
                    { x: 0, y: 0 },
                    { x: 1, y: 0 },
                    { x: 1, y: 1 },
                    { x: 0, y: 1 },
                ],
            };
            expect(isPolygonValid(polygonShape)).toBe(false);
        });

        it('should handle null polygons', () => {
            expect(isPolygonValid(null)).toBe(false);
        });
    });

    describe('getShapesUnion', () => {
        it('should return the union of two shapes', () => {
            const roi = { x: 0, y: 0, width: 100, height: 100 };
            const shape1: Rect = { x: 0, y: 0, width: 10, height: 10, shapeType: ShapeType.Rect };
            const shape2: Rect = { x: 5, y: 5, width: 10, height: 10, shapeType: ShapeType.Rect };
            const unionShape = getShapesUnion(roi, shape1, shape2);

            expect(unionShape.points).toBeDefined();
        });

        it('should handle shapes with no intersection', () => {
            const roi = { x: 0, y: 0, width: 100, height: 100 };
            const shape1: Rect = { x: 0, y: 0, width: 10, height: 10, shapeType: ShapeType.Rect };
            const shape2: Rect = { x: 50, y: 50, width: 10, height: 10, shapeType: ShapeType.Rect };
            const unionShape = getShapesUnion(roi, shape1, shape2);

            expect(unionShape.points).toBeDefined();
        });
    });

    describe('isShapePartiallyWithinROI', () => {
        it('should return true if the shape is partially within the ROI', () => {
            const roi = { x: 0, y: 0, width: 100, height: 100 };
            const shape: Rect = { x: 90, y: 90, width: 20, height: 20, shapeType: ShapeType.Rect };

            expect(isShapePartiallyWithinROI(roi, shape)).toBe(true);
        });

        it('should return false if the shape is completely outside the ROI', () => {
            const roi = { x: 0, y: 0, width: 100, height: 100 };
            const shape: Rect = { x: 150, y: 150, width: 20, height: 20, shapeType: ShapeType.Rect };

            expect(isShapePartiallyWithinROI(roi, shape)).toBe(false);
        });

        it('should return false if the shape is fully within the ROI', () => {
            const roi = { x: 0, y: 0, width: 100, height: 100 };
            const shape: Rect = { x: 10, y: 10, width: 20, height: 20, shapeType: ShapeType.Rect };

            expect(isShapePartiallyWithinROI(roi, shape)).toBe(false);
        });
    });

    describe('isShapeWithinRoi', () => {
        const roi = { x: 0, y: 0, width: 100, height: 100 };

        it('inside', () => {
            const circle: Circle = { x: 10, y: 10, r: 20, shapeType: ShapeType.Circle };
            expect(isShapeWithinRoi(roi, circle)).toBe(true);
        });

        it('outside', () => {
            const circle: Circle = { x: -21, y: 0, r: 20, shapeType: ShapeType.Circle };
            expect(isShapeWithinRoi(roi, circle)).toBe(false);
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
            expect(calculatePolygonArea(shapeToTurfPolygon(rioRect))).toBeGreaterThan(
                calculatePolygonArea(shapeToTurfPolygon(newShape))
            );
            expect(newShape.shapeType).toBe(ShapeType.Polygon);
        });
    });

    describe('calculatePolygonArea', () => {
        it('should calculate the area of a valid polygon', () => {
            const turfPolygon: TurfPolygon = {
                type: 'Feature',
                geometry: {
                    type: 'Polygon',
                    coordinates: [
                        [
                            [0, 0],
                            [10, 0],
                            [10, 10],
                            [0, 10],
                            [0, 0], // Closing the polygon
                        ],
                    ],
                },
                properties: {},
            };

            const area = calculatePolygonArea(turfPolygon);
            expect(area).toBe(100); // 10x10 square
        });

        it('should return 0 for a polygon with no area', () => {
            const turfPolygon: TurfPolygon = {
                type: 'Feature',
                geometry: {
                    type: 'Polygon',
                    coordinates: [
                        [
                            [0, 0],
                            [0, 0],
                            [0, 0],
                            [0, 0],
                            [0, 0], // Closing the polygon
                        ],
                    ],
                },
                properties: {},
            };

            const area = calculatePolygonArea(turfPolygon);
            expect(area).toBe(0);
        });

        it('should handle polygons with negative coordinates', () => {
            const turfPolygon: TurfPolygon = {
                type: 'Feature',
                geometry: {
                    type: 'Polygon',
                    coordinates: [
                        [
                            [-10, -10],
                            [0, -10],
                            [0, 0],
                            [-10, 0],
                            [-10, -10], // Closing the polygon
                        ],
                    ],
                },
                properties: {},
            };

            const area = calculatePolygonArea(turfPolygon);
            expect(area).toBe(100); // 10x10 square
        });
    });

    describe('findLargestPolygon', () => {
        it('should return the largest polygon from a MultiPolygon', () => {
            const multiPolygon: Feature<MultiPolygon> = {
                type: 'Feature',
                geometry: {
                    type: 'MultiPolygon',
                    coordinates: [
                        [
                            [
                                [0, 0],
                                [5, 0],
                                [5, 5],
                                [0, 5],
                                [0, 0],
                            ],
                        ],
                        [
                            [
                                [0, 0],
                                [10, 0],
                                [10, 10],
                                [0, 10],
                                [0, 0],
                            ],
                        ],
                    ],
                },
                properties: {},
            };

            const largestPolygon = findLargestPolygon(multiPolygon);
            const largestArea = calculatePolygonArea(largestPolygon);

            expect(largestArea).toBe(100); // 10x10 square
        });
    });

    describe('calculateCirclePoints', () => {
        it('should generate points forming a circle with correct count and closure', () => {
            const circle: Circle = { x: 0, y: 0, r: 10, shapeType: ShapeType.Circle };
            const points = calculateCirclePoints(circle);

            // 360/5 = 72 steps, plus the initial point at 0, so 73 points
            expect(points.length).toHaveLength(73);

            // First and last points should be the same (circle closure)
            expect(points[0][0]).toBeCloseTo(points[points.length - 1][0], 5);
            expect(points[0][1]).toBeCloseTo(points[points.length - 1][1], 5);
        });

        it('should generate all points at the correct radius from center', () => {
            const circle: Circle = { x: 5, y: -3, r: 7, shapeType: ShapeType.Circle };
            const points = calculateCirclePoints(circle);

            for (let i = 0; i < points.length; i++) {
                const [x, y] = points[i];
                const dx = x - circle.x;
                const dy = y - circle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                expect(distance).toBeCloseTo(circle.r, 5);
            }
        });

        it('should handle zero radius', () => {
            const circle: Circle = { x: 2, y: 2, r: 0, shapeType: ShapeType.Circle };
            const points = calculateCirclePoints(circle);

            expect(points.length).toHaveLength(73);
            points.forEach(([x, y]) => {
                expect(x).toBeCloseTo(2, 5);
                expect(y).toBeCloseTo(2, 5);
            });
        });
    });
});
