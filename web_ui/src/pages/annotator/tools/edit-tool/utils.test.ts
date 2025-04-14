// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getBoundingBoxInRoi, getBoundingBoxResizePoints, getClampedBoundingBox } from './utils';

const mockedRoi = {
    x: 0,
    y: 0,
    width: 100,
    height: 100,
};

describe('edit-tool utils', () => {
    describe('getClampedBoundingBox', () => {
        const mockedBoundingBox = { x: 0, y: 0, width: 20, height: 20 };
        test.each([
            [{ x: 0, y: 0 }, mockedBoundingBox, { ...mockedBoundingBox, x: mockedRoi.x, y: mockedRoi.y }], // No clamping needed
            [{ x: mockedRoi.width, y: mockedRoi.height }, mockedBoundingBox, { ...mockedBoundingBox, x: 80, y: 80 }], // Clamped outside bottom-right
            [{ x: -10, y: -10 }, mockedBoundingBox, { ...mockedBoundingBox }], // Clamped outside top-left
        ])('given point %o move the boundingBox %o to %o', (point, boundingBox, expectedResult) => {
            const result = getClampedBoundingBox(point, boundingBox, mockedRoi);
            expect(result).toEqual(expectedResult);
        });
    });

    describe('getBoundingBoxInRoi', () => {
        const mockedBoundingBox = { x: 0, y: 0, width: 10, height: 10 };

        test.each([
            [mockedBoundingBox, mockedBoundingBox], // Completely inside ROI
            [{ ...mockedBoundingBox, x: -10 }, mockedBoundingBox], // Partially outside left
            [
                { ...mockedBoundingBox, x: 95 },
                { ...mockedBoundingBox, x: 95, width: 5 }, // Partially outside right
            ],
            [{ ...mockedBoundingBox, y: -10 }, mockedBoundingBox], // Partially outside top
            [
                { ...mockedBoundingBox, y: 95 },
                { ...mockedBoundingBox, y: 95, height: 5 }, // Partially outside bottom
            ],
        ])('given boundingBox %o, returns the portion inside the roi %o', (boundingBox, expectedResult) => {
            const result = getBoundingBoxInRoi(boundingBox, mockedRoi);
            expect(result).toEqual(expectedResult);
        });
    });

    describe('getBoundingBoxResizePoints', () => {
        it('should create resize points with correct properties', () => {
            const gap = 0;
            const boundingBox = { x: 50, y: 50, width: 50, height: 50 };
            const resizePoints = getBoundingBoxResizePoints({ boundingBox, gap, onResized: jest.fn() });

            const expectedAnchors = [
                { x: 50, y: 50, cursor: 'nw-resize', label: 'North west resize anchor' },
                { x: 75, y: 50, cursor: 'n-resize', label: 'North resize anchor' },
                { x: 100, y: 50, cursor: 'ne-resize', label: 'North east resize anchor' },
                { x: 100, y: 75, cursor: 'e-resize', label: 'East resize anchor' },
                { x: 100, y: 100, cursor: 'se-resize', label: 'South east resize anchor' },
                { x: 75, y: 100, cursor: 's-resize', label: 'South resize anchor' },
                { x: 50, y: 100, cursor: 'sw-resize', label: 'South west resize anchor' },
                { x: 50, y: 75, cursor: 'w-resize', label: 'West resize anchor' },
            ];

            expect(resizePoints).toHaveLength(8);
            expectedAnchors.forEach((expected, index) => {
                expect(resizePoints[index]).toMatchObject(expected);
            });
        });

        describe('getBoundingBoxResizePoints', () => {
            const gap = 0;
            const onResized = jest.fn();
            const boundingBox = { x: 50, y: 50, width: 50, height: 50 };
            const resizePoints = getBoundingBoxResizePoints({ boundingBox, gap, onResized });
            const [
                topLeftPoint,
                topCenterPoint,
                topRightPoint,
                rightCenterPoint,
                bottomRightPoint,
                bottomCenterPoint,
                bottomLeftPoint,
                centerLeftPoint,
            ] = resizePoints;

            const testCases = [
                {
                    index: 0,
                    moveTo: [topLeftPoint.x - 50, 0], // Move NW anchor 50 units left and up
                    expected: { x: 0, y: 0, width: 100, height: 100 },
                    description: 'topLeftPoint',
                },
                {
                    index: 1,
                    moveTo: [topCenterPoint.x - 50, 0], // Move N anchor 50 units up
                    expected: { x: 50, y: 0, width: 50, height: 100 },
                    description: 'topCenterPoint',
                },
                {
                    index: 2,
                    moveTo: [topRightPoint.x + 50, 0], // Move NE anchor 50 units up
                    expected: { x: 50, y: 0, width: 100, height: 100 },
                    description: 'topRightPoint',
                },
                {
                    index: 3,
                    moveTo: [rightCenterPoint.x + 50, 0], // Move E anchor 50 units right
                    expected: { x: 50, y: 50, width: 100, height: 50 },
                    description: 'rightCenterPoint',
                },
                {
                    index: 4,
                    moveTo: [bottomRightPoint.x + 50, bottomRightPoint.y + 50], // Move SE anchor 50 units down and right
                    expected: { x: 50, y: 50, width: 100, height: 100 },
                    description: 'bottomRightPoint',
                },
                {
                    index: 5,
                    moveTo: [0, bottomCenterPoint.y + 50], // Move S anchor 50 units down
                    expected: { x: 50, y: 50, width: 50, height: 100 },
                    description: 'bottomCenterPoint',
                },
                {
                    index: 6,
                    moveTo: [0, bottomLeftPoint.y + 50], // Move SW anchor 50 units down and left
                    expected: { x: 0, y: 50, width: 100, height: 100 },
                    description: 'bottomLeftPoint',
                },

                {
                    index: 7,
                    moveTo: [centerLeftPoint.x - 50, 0], // Move W anchor 50 units left
                    expected: { x: 0, y: 50, width: 100, height: 50 },
                    description: 'centerLeftPoint',
                },
            ];

            test.each(testCases)('$description moves and resizes correctly', ({ index, moveTo, expected }) => {
                const [x, y] = moveTo;
                resizePoints[index].moveAnchorTo(x, y);
                expect(onResized).toHaveBeenCalledWith(expected);
            });
        });

        it('should not go below gap', () => {
            const gap = 20;
            const onResized = jest.fn();
            const boundingBox = { x: 50, y: 50, width: 50, height: 50 };
            const resizePoints = getBoundingBoxResizePoints({ boundingBox, gap, onResized });

            resizePoints[3].moveAnchorTo(-100, 0);

            expect(onResized).toHaveBeenCalledWith({ ...boundingBox, width: gap });
        });

        it('clamp to minimum 0 for coordinates', () => {
            const gap = 20;
            const onResized = jest.fn();
            const boundingBox = { x: 50, y: 50, width: 50, height: 50 };
            const resizePoints = getBoundingBoxResizePoints({ boundingBox, gap, onResized });

            resizePoints[6].moveAnchorTo(-10, -10);

            expect(onResized).toHaveBeenCalledWith({ x: 0, width: 100, y: 50, height: gap });
        });
    });
});
