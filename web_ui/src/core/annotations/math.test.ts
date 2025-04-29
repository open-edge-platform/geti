// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getImageData } from '../../shared/canvas-utils';
import { getMockedLabel } from '../../test-utils/mocked-items-factory/mocked-labels';
import {
    BoundingBox,
    calculateDistance,
    clampBetween,
    clampBox,
    clampPointBetweenImage,
    degreesToRadians,
    getBoundingBox,
    getCenterOfShape,
    getIntersectionPoint,
    getShapesBoundingBox,
    hasEqualBoundingBox,
    isInsideOfBoundingBox,
    isPointInShape,
    isPointOverPoint,
    isValueBetween,
    pointInCircle,
    pointInPolygon,
    pointInRectangle,
    pointInRotatedRectangle,
    pointsToRect,
    radiansToDegrees,
    roiFromImage,
    sgn,
} from './math';
import { Circle, Point, Polygon, Rect, RotatedRect, Shape } from './shapes.interface';
import { ShapeType } from './shapetype.enum';
import { labelFromUser } from './utils';

describe('degreesToRadians', () => {
    const testInputs = [
        [0, 0],
        [360, 2 * Math.PI],
        [180, Math.PI],
        [-180, -Math.PI],
    ];

    test.each(testInputs)('%s degrees equals %s radians', (degrees, expectedRadians) => {
        expect(degreesToRadians(degrees)).toEqual(expectedRadians);
    });
});

describe('radiansToDegrees', () => {
    const testInputs = [
        [0, 0, 0],
        [2 * Math.PI, 360],
        [Math.PI, 180],
        [-Math.PI, -180],
    ];

    test.each(testInputs)('%s radians equals %s degrees', (radians, expectedDegrees) => {
        expect(radiansToDegrees(radians)).toEqual(expectedDegrees);
    });
});

describe('clampBetween', () => {
    const testInputs = [
        [0, 0.5, 1, 0.5],
        [0, 2, 1, 1],
        [0, -1, 1, 0],
    ];

    test.each(testInputs)('clampBetween(%s, %s, %s) should equal %s', (min, value, max, expectedResult) => {
        expect(clampBetween(min, value, max)).toEqual(expectedResult);
    });
});

describe('pointsToRect', () => {
    it('takes two points and returns area in between the points', () => {
        const subject = pointsToRect({ x: 10, y: 10 }, { x: 20, y: 20 });
        expect(subject).toEqual({ x: 10, y: 10, width: 10, height: 10 });
    });

    it('does not care about order of points', () => {
        const subject = pointsToRect({ x: 20, y: 20 }, { x: 10, y: 10 });
        expect(subject).toEqual({ x: 10, y: 10, width: 10, height: 10 });
    });

    it('can return a region of interest of 0 width and height', () => {
        const subject = pointsToRect({ x: 10, y: 10 }, { x: 10, y: 10 });
        expect(subject).toEqual({ x: 10, y: 10, width: 0, height: 0 });
    });
});

describe('calculateDistance', () => {
    const testData: [Point, Point, number][] = [
        [{ x: 0, y: 0 }, { x: 100, y: 0 }, 100],
        [{ x: 0, y: 0 }, { x: 0, y: 100 }, 100],
        [{ x: 100, y: 0 }, { x: 0, y: 0 }, 100],
        [{ x: 0, y: 100 }, { x: 0, y: 0 }, 100],
        [{ x: 0, y: 0 }, { x: 100, y: 100 }, 100 * Math.sqrt(2)],
        [{ x: 0, y: 0 }, { x: -100, y: -100 }, 100 * Math.sqrt(2)],
    ];

    test.each(testData)(
        'expect distance between %s and %s to equal %s',
        (p1: Point, p2: Point, expectedDistance: number) => {
            expect(calculateDistance(p1, p2)).toEqual(expectedDistance);
        }
    );
});

describe('roiFromImage', () => {
    it('takes dimensions and offsets of an image to create a region of interest', () => {
        const subject = roiFromImage(getImageData(new Image(200, 100)));

        // offsets are not tested
        expect(subject.width).toEqual(200);
        expect(subject.height).toEqual(100);
    });
});

describe('clampPointBetweenImage', () => {
    describe('creates a curried function to clamp points within the image', () => {
        const fakeImage = getImageData(new Image(200, 100));
        const subject = clampPointBetweenImage(fakeImage);
        const testData = [
            [
                { x: 0, y: 0 },
                { x: 0, y: 0 },
            ],
            [
                { x: -100, y: 0 },
                { x: 0, y: 0 },
            ],
            [
                { x: 300, y: -100 },
                { x: 200, y: 0 },
            ],
            [
                { x: 300, y: 300 },
                { x: 200, y: 100 },
            ],
        ];
        test.each(testData)('and func(%s) should equal %s', (point, expectedValue) => {
            expect(subject(point)).toEqual(expectedValue);
        });
    });
});

describe('isPointOverPoint', () => {
    const testData: [Point, Point, number, boolean][] = [
        [{ x: 20, y: 20 }, { x: 30, y: 20 }, 20, true],
        [{ x: 20, y: 20 }, { x: 30, y: 20 }, 5, false],
    ];

    test.each(testData)('tests if %s overlaps %s when p1 radius is %s', (p1, p2, p1_radius, expectedResult) => {
        expect(isPointOverPoint(p1, p2, p1_radius)).toEqual(expectedResult);
    });
});

describe('isValueBetween', () => {
    const testData: [number, number, number, boolean][] = [
        [3, 1, 5, true],
        [1, 1, 5, true],
        [5, 1, 5, true],
        [0, 1, 5, false],
        [10, 1, 5, false],
        [10, -10, 0, false],
        [-5, -10, 0, true],
        [-20, -10, 0, false],
    ];
    test.each(testData)('tests if %s is within %s and %s', (value, a, b, expectedResult) => {
        expect(isValueBetween(value, a, b)).toBe(expectedResult);
    });
});

describe('sgn', () => {
    const testData: [number, number][] = [
        [-5.4, -1],
        [100.3, 1],
        [0, 1],
        [Infinity, 1],
        [-Infinity, -1],
    ];

    test.each(testData)('sign of %s to equal %s', (value, expectedSign) => {
        expect(sgn(value)).toEqual(expectedSign);
    });
});

describe('getIntersectionPoint', () => {
    describe('tries to find a point where a line is within radius of a point', () => {
        const pointList = [
            // square (roi of 0, 0, 50, 50)
            { x: 0, y: 0 },
            { x: 50, y: 0 },
            { x: 50, y: 50 },
            { x: 0, y: 50 },
        ];

        it('returns the second point in list when point is placed between point 1 and point 2', () => {
            const subject = getIntersectionPoint(1, { x: 25, y: 0 }, pointList);
            expect(subject).toEqual({ x: 50, y: 0 });
        });

        it('returns null when point is not intersecting any lines between points', () => {
            const subject = getIntersectionPoint(5, { x: 25, y: 25 }, pointList);
            expect(subject).toBeNull();
        });

        it('returns null when point is huge and encompassing all lines', () => {
            // Not sure if this is intended....
            const subject = getIntersectionPoint(1000, { x: 25, y: 25 }, pointList);
            expect(subject).toBeNull();
        });
    });
});

describe('pointInRectangle', () => {
    const rectangle: Rect = { x: 100, y: 100, width: 500, height: 250, shapeType: ShapeType.Rect };
    const testData: [Point, boolean][] = [
        [{ x: 50, y: 50 }, false],
        [{ x: 200, y: 250 }, true],
        [{ x: 2000, y: 250 }, false],
    ];
    test.each(testData)(`tests if %s falls within test rectangle (%s)`, (point, expectedResult) => {
        expect(pointInRectangle(rectangle, point)).toBe(expectedResult);
    });
});

describe('pointInRotatedRectangle', () => {
    const rotatedRect: RotatedRect = {
        x: 50,
        y: 50,
        width: 100,
        height: 50,
        angle: 90,
        shapeType: ShapeType.RotatedRect,
    };

    const testData: [Point, boolean][] = [
        [{ x: 50, y: 50 }, true],
        [{ x: 0, y: 0 }, false],
        [{ x: 50, y: -10 }, false],
        [{ x: 50, y: 1 }, true],
    ];

    test.each(testData)('tests if point %s is within rotated rect (%s)', (point, expectedResult) => {
        expect(pointInRotatedRectangle(rotatedRect, point)).toBe(expectedResult);
    });
});

describe('pointInCircle', () => {
    const circle: Circle = { x: 50, y: 50, r: 20, shapeType: ShapeType.Circle };
    const testData: [Point, boolean][] = [
        [{ x: 0, y: 0 }, false],
        [{ x: 50, y: 50 }, true],
        [{ x: 70, y: 50 }, false],
        [{ x: 50, y: 70 }, false],
        [{ x: 64, y: 64 }, true],
        [{ x: 65, y: 65 }, false],
    ];
    test.each(testData)('tests if point %s is within circle (%s)', (point, expectedResult) => {
        expect(pointInCircle(circle, point)).toBe(expectedResult);
    });
});

describe('pointInPolygon', () => {
    describe('simple rectangle polygon', () => {
        const polygon: Polygon = {
            shapeType: ShapeType.Polygon,
            points: [
                { x: 0, y: 0 },
                { x: 50, y: 0 },
                { x: 50, y: 50 },
                { x: 0, y: 50 },
            ],
        };
        const testData: [Point, boolean][] = [
            [{ x: 25, y: 25 }, true],
            [{ x: 50, y: 0 }, false],
            [{ x: -1, y: 0 }, false],
        ];
        test.each(testData)('tests if point %s is within polygon (%s)', (point, expectedResult) => {
            expect(pointInPolygon(polygon, point)).toEqual(expectedResult);
        });
    });
    describe('concave polygon', () => {
        const polygon: Polygon = {
            shapeType: ShapeType.Polygon,
            points: [
                { x: 0, y: 0 },
                { x: 50, y: 0 },
                { x: 50, y: 50 },
                { x: 100, y: 50 },
                { x: 100, y: 0 },
                { x: 150, y: 0 },
                { x: 140, y: 100 },
                { x: 0, y: 100 },
            ],
        };
        const testData: [Point, boolean][] = [
            [{ x: 75, y: 75 }, true],
            [{ x: 75, y: 25 }, false],
            [{ x: 145, y: 50 }, false],
            [{ x: 140, y: 50 }, true],
            [{ x: 75, y: 120 }, false],
        ];
        test.each(testData)('tests if point %s is within polygon (%s)', (point, expectedResult) => {
            expect(pointInPolygon(polygon, point)).toEqual(expectedResult);
        });
    });
});

describe('isPointInShape', () => {
    const testData: [Shape, Point, boolean][] = [
        [
            {
                shapeType: ShapeType.Polygon,
                points: [
                    { x: 0, y: 0 },
                    { x: 50, y: 0 },
                    { x: 50, y: 50 },
                    { x: 0, y: 50 },
                ],
            },
            { x: 25, y: 25 },
            true,
        ],
        [{ x: 100, y: 100, width: 500, height: 250, shapeType: ShapeType.Rect }, { x: 50, y: 50 }, false],
        [{ x: 50, y: 50, r: 20, shapeType: ShapeType.Circle }, { x: 50, y: 50 }, true],
        [
            {
                x: 50,
                y: 50,
                width: 100,
                height: 50,
                angle: 90,
                shapeType: ShapeType.RotatedRect,
            },
            { x: 50, y: 50 },
            true,
        ],
    ];
    test.each(testData)('tests if point %s is within given shape (%s)', (shape, point, expectedResult) => {
        expect(isPointInShape(shape, point)).toEqual(expectedResult);
    });
});

describe('getBoundingBox functions', () => {
    const boundingBoxTestInputs: [Shape, Omit<Rect, 'shapeType'>][] = [
        [
            { x: 0, y: 0, width: 100, height: 100, shapeType: ShapeType.Rect },
            { x: 0, y: 0, width: 100, height: 100 },
        ],
        [
            { x: 150, y: 150, r: 50, shapeType: ShapeType.Circle },
            { x: 100, y: 100, width: 100, height: 100 },
        ],
        [
            {
                points: [
                    { x: 0, y: 200 },
                    { x: 100, y: 200 },
                    { x: 100, y: 300 },
                ],
                shapeType: ShapeType.Polygon,
            },
            { x: 0, y: 200, width: 100, height: 100 },
        ],
        [
            {
                points: [
                    {
                        x: 0,
                        y: 0,
                        isVisible: true,
                        label: labelFromUser(getMockedLabel({ name: 'head' })),
                    },
                    {
                        x: 100,
                        y: 200,
                        isVisible: true,
                        label: labelFromUser(getMockedLabel({ name: 'nose' })),
                    },
                    {
                        x: 100,
                        y: 300,
                        isVisible: true,
                        label: labelFromUser(getMockedLabel({ name: 'nose' })),
                    },
                ],
                shapeType: ShapeType.Pose,
            },
            { x: 0, y: 0, width: 100, height: 300 },
        ],
    ];

    describe('getBoundingBox', () => {
        test.each(boundingBoxTestInputs)(
            'finds the bounding box of a shape',
            (shape: Shape, boundingBox: Omit<Rect, 'shapeType'>): void => {
                expect(getBoundingBox(shape)).toEqual(boundingBox);
            }
        );

        it('finds the bounding box of rotated rect', () => {
            const rotatedRect: RotatedRect = {
                x: 100,
                y: 100,
                width: 200,
                height: 100,
                angle: 90,
                shapeType: ShapeType.RotatedRect,
            };
            const expectedBoundingBox = { x: 50, y: 0, width: 100, height: 200 };
            const subject = getBoundingBox(rotatedRect);
            expect(subject.x).toBeCloseTo(expectedBoundingBox.x);
            expect(subject.y).toBeCloseTo(expectedBoundingBox.y);
            expect(subject.width).toBeCloseTo(expectedBoundingBox.width);
            expect(subject.height).toBeCloseTo(expectedBoundingBox.height);
        });
    });

    describe('getShapesBoundingBox', () => {
        it('finds the bounding box of a collection of shapes', () => {
            expect(getShapesBoundingBox(boundingBoxTestInputs.map(([shape]) => shape))).toEqual({
                x: 0,
                y: 0,
                width: 200,
                height: 300,
            });
        });
    });
});

describe('isInsideOfBoundingBox', () => {
    it.each([
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 0, y: 0, width: 10, height: 10 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 90, y: 90, width: 10, height: 10 },
        ],
    ])('%s contains %s', (first, second) => {
        expect(isInsideOfBoundingBox(first, second)).toEqual(true);
    });

    it.each([
        // Outside of corners,
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: -20, y: -20, width: 10, height: 10 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 0, y: -20, width: 10, height: 10 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 120, y: -20, width: 10, height: 10 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 120, y: 0, width: 10, height: 10 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 120, y: 120, width: 10, height: 10 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 0, y: 120, width: 10, height: 10 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: -20, y: 120, width: 10, height: 10 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: -20, y: 0, width: 10, height: 10 },
        ],
        // Partially outside, partially inside
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: -10, y: -10, width: 20, height: 20 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 0, y: -10, width: 20, height: 20 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 110, y: -10, width: 20, height: 20 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 110, y: 0, width: 20, height: 20 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 110, y: 110, width: 20, height: 20 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: 0, y: 110, width: 20, height: 20 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: -10, y: 110, width: 20, height: 20 },
        ],
        [
            { x: 0, y: 0, width: 100, height: 100 },
            { x: -10, y: 0, width: 20, height: 20 },
        ],
    ])('%s does not contain %s', (first, second) => {
        expect(isInsideOfBoundingBox(first, second)).toEqual(false);
    });
});

describe('getCenterOfShape', () => {
    const testData: [Shape, Point][] = [
        [
            {
                shapeType: ShapeType.Polygon,
                points: [
                    { x: 0, y: 0 },
                    { x: 50, y: 0 },
                    { x: 50, y: 50 },
                    { x: 0, y: 50 },
                ],
            },
            { x: 25, y: 25 },
        ],
        [
            {
                shapeType: ShapeType.Circle,
                x: 25,
                y: 25,
                r: 100,
            },
            { x: 25, y: 25 },
        ],
        [
            {
                shapeType: ShapeType.Rect,
                x: 100,
                y: 0,
                width: 100,
                height: 100,
            },
            { x: 150, y: 50 },
        ],
        [
            {
                shapeType: ShapeType.RotatedRect,
                x: 100,
                y: 100,
                width: 200,
                height: 100,
                angle: 90,
            },
            { x: 100, y: 100 },
        ],
    ];

    test.each(testData)('returns shape %s center of %s', (shape, expectedCenter) => {
        expect(getCenterOfShape(shape)).toEqual(expectedCenter);
    });
});

describe('hasEqualBoundingBox', () => {
    const boundingBox = {
        x: 0,
        y: 0,
        width: 100,
        height: 100,
    };
    const testData: [BoundingBox, boolean][] = [
        [{ x: 0, y: 0, width: 100, height: 100 }, true],
        [{ x: 1, y: 0, width: 100, height: 100 }, false],
        [{ x: 0, y: -1, width: 100, height: 100 }, false],
        [{ x: 0, y: 0, width: 5, height: 100 }, false],
        [{ x: 0, y: 0, width: 100, height: 2000 }, false],
    ];

    test.each(testData)('test if %s equals the test boundingBox (%s)', (second, expectedResult) => {
        expect(hasEqualBoundingBox(boundingBox, second)).toEqual(expectedResult);
    });
});

describe('clampBox', () => {
    const area = { x: 50, y: 20, width: 350, height: 380 };

    const r = (x: number, y: number, width: number, height: number) => {
        return { x, y, width, height };
    };

    it('clamps box when above area', () => {
        const subject = clampBox(r(-100, -100, 200, 200), area);
        expect(subject).toEqual(r(50, 20, 50, 80));
    });

    it('clamps box when left of area', () => {
        const subject = clampBox(r(300, 300, 200, 200), area);
        expect(subject).toEqual(r(300, 300, 100, 100));
    });

    it('clamps box dimensions when bigger than area', () => {
        const subject = clampBox(r(0, 0, 600, 600), area);
        expect(subject).toEqual(area);
    });
});
