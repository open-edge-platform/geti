// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeypointStructure } from '../../../../core/projects/task.interface';
import { getMockedKeypointNode } from '../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import {
    CursorDirection,
    getAnnotationInBoundingBox,
    getDirection,
    getInnerPaddedBoundingBox,
    getOuterPaddedBoundingBox,
    getPercentageFromPoint,
    getPointFromPercentage,
    getPointsEdges,
    getPoseLocations,
    getTemplateWithDirection,
    groupByFirstNode,
    mirrorPointsAcrossAxis,
    PADDING_MULTIPLIER,
    PointAxis,
    rotatePointsAroundPivot,
} from './utils';

describe('keypoint-tool utils', () => {
    it('getPercentageFromPoint', () => {
        const roi = { x: 0, y: 0, width: 20, height: 20 };
        expect(getPercentageFromPoint({ x: 20, y: 20 }, roi)).toEqual({ x: 100, y: 100 });
        expect(getPercentageFromPoint({ x: 10, y: 10 }, roi)).toEqual({ x: 50, y: 50 });

        const offsetRoi = { x: 20, y: 20, width: 20, height: 20 };
        expect(getPercentageFromPoint({ x: 20, y: 20 }, offsetRoi)).toEqual({ x: 0, y: 0 });
        expect(getPercentageFromPoint({ x: 40, y: 40 }, offsetRoi)).toEqual({ x: 100, y: 100 });
    });

    it('getPointFromPercentage', () => {
        const roi = { x: 0, y: 0, width: 20, height: 20 };
        expect(getPointFromPercentage({ x: 50, y: 50 }, roi)).toEqual({ x: 10, y: 10 });
        expect(getPointFromPercentage({ x: 100, y: 100 }, roi)).toEqual({ x: 20, y: 20 });
    });

    describe('getOuterPaddedBoundingBox', () => {
        it('large ROIs, calculates the padding using the PADDING_MULTIPLIER', () => {
            const roi = { x: PADDING_MULTIPLIER, y: PADDING_MULTIPLIER, width: 1000, height: 1000 };
            expect(getOuterPaddedBoundingBox(roi, 1)).toEqual({
                x: 0,
                y: 0,
                width: roi.width + PADDING_MULTIPLIER * 2,
                height: roi.height + PADDING_MULTIPLIER * 2,
            });
        });

        it('small ROIs, calculates the padding based on the smallest side', () => {
            const smallestSide = 20;
            const padding = smallestSide * 0.1;
            const roi = { x: padding, y: padding, width: smallestSide, height: 40 };

            expect(getOuterPaddedBoundingBox(roi, 1)).toEqual({
                x: 0,
                y: 0,
                width: roi.width + padding * 2,
                height: roi.height + padding * 2,
            });
        });
    });

    describe('getInnerPaddedBoundingBox', () => {
        it('large ROIs, calculates the padding using the PADDING_MULTIPLIER', () => {
            const roi = { x: 0, y: 0, width: 1000, height: 1000 };
            expect(getInnerPaddedBoundingBox(roi, 1)).toEqual({
                x: PADDING_MULTIPLIER,
                y: PADDING_MULTIPLIER,
                width: roi.width - PADDING_MULTIPLIER * 2,
                height: roi.height - PADDING_MULTIPLIER * 2,
            });
        });

        it('small ROIs, calculates the padding based on the smallest side', () => {
            const smallestSide = 20;
            const padding = smallestSide * 0.1;
            const roi = { x: 0, y: 0, width: smallestSide, height: 40 };

            expect(getInnerPaddedBoundingBox(roi, 1)).toEqual({
                x: padding,
                y: padding,
                width: roi.width - padding * 2,
                height: roi.height - padding * 2,
            });
        });
    });

    describe('getAnnotationInBoundingBox', () => {
        it.each([
            [
                [
                    { x: 0, y: 0 },
                    { x: 100, y: 100 },
                ],
                { x: 100, y: 100, width: 100, height: 100 },
            ],
            [
                [
                    { x: 20, y: 20 },
                    { x: 100, y: 100 },
                ],
                { x: 0, y: 0, width: 200, height: 200 },
            ],
        ])('%s annotation is positioned within the new ROI boundaries', (points, roi) => {
            const newAnnotation = getAnnotationInBoundingBox(
                points.map((point) => ({
                    ...point,
                    label: getMockedLabel({ name: 'head' }),
                    edgeEnds: [],
                    isVisible: true,
                    isSelected: false,
                })),
                roi
            );

            newAnnotation.shape.points.forEach((point) => {
                expect(point.x).toBeGreaterThanOrEqual(roi.x);
                expect(point.y).toBeGreaterThanOrEqual(roi.y);
                expect(point.x - roi.x).toBeLessThanOrEqual(roi.width);
                expect(point.y - roi.y).toBeLessThanOrEqual(roi.height);
            });
        });
    });

    describe('groupByFirstNode', () => {
        it('groups edges by the first node', () => {
            expect(groupByFirstNode([{ nodes: ['A', 'B'] }, { nodes: ['A', 'C'] }, { nodes: ['B', 'D'] }])).toEqual({
                A: ['B', 'C'],
                B: ['D'],
            });
        });

        it('groups duplicate edges correctly', () => {
            expect(groupByFirstNode([{ nodes: ['A', 'B'] }, { nodes: ['A', 'B'] }, { nodes: ['A', 'C'] }])).toEqual({
                A: ['B', 'C'],
            });
        });

        it('nodes sharing the same second label', () => {
            const result = groupByFirstNode([{ nodes: ['A', 'B'] }, { nodes: ['C', 'B'] }, { nodes: ['D', 'B'] }]);
            expect(result).toEqual({
                A: ['B'],
                C: ['B'],
                D: ['B'],
            });
        });

        it('remove self-loop values', () => {
            const result = groupByFirstNode([{ nodes: ['A', 'B'] }, { nodes: ['A', 'A'] }]);

            expect(result).toEqual({ A: ['B'] });
        });

        it('remove invalid values', () => {
            const skeleton = [{ nodes: ['A', 'B'] }, { nodes: [] }, { nodes: ['C'] }] as KeypointStructure['edges'];
            const result = groupByFirstNode(skeleton);

            expect(result).toEqual({
                A: ['B'],
                C: [],
            });
        });
    });

    describe('getPointsEdges', () => {
        const labelA = getMockedLabel({ id: 'A' });
        const labelB = getMockedLabel({ id: 'B' });
        const labelC = getMockedLabel({ id: 'C' });

        const nodeA = { label: labelA, x: 0, y: 0, edgeEnds: [], isVisible: true, isSelected: false };
        const nodeB = { label: labelB, x: 10, y: 10, edgeEnds: [], isVisible: true, isSelected: false };
        const nodeX = { label: labelC, x: 20, y: 20, edgeEnds: [], isVisible: true, isSelected: false };

        it('returns edges with points connected by their labels', () => {
            const keypointNodes = [nodeA, nodeB, nodeX];

            const result = getPointsEdges(keypointNodes, [
                { nodes: [labelA.id, labelB.id] },
                { nodes: [labelA.id, labelC.id] },
            ]);

            expect(result).toEqual([
                { from: { labelId: labelA.id, x: 0, y: 0 }, to: { labelId: labelB.id, x: 10, y: 10 } },
                { from: { labelId: labelA.id, x: 0, y: 0 }, to: { labelId: labelC.id, x: 20, y: 20 } },
            ]);
        });

        it('removes duplicate edges', () => {
            const keypointNodes = [nodeA, nodeB];

            const result = getPointsEdges(keypointNodes, [
                { nodes: [labelA.id, labelB.id] },
                { nodes: [labelA.id, labelB.id] },
            ]);

            expect(result).toEqual([
                { from: { labelId: labelA.id, x: 0, y: 0 }, to: { labelId: labelB.id, x: 10, y: 10 } },
            ]);
        });

        it('nodes without corresponding edges', () => {
            const result = getPointsEdges([nodeA], []);

            expect(result).toEqual([]);
        });
    });

    describe('mirrorPointsAcrossAxis', () => {
        it('mirror points across the X axis', () => {
            const mirroredPoints = mirrorPointsAcrossAxis(
                [
                    { x: 1, y: 2 },
                    { x: 3, y: 4 },
                    { x: 5, y: 6 },
                ],
                PointAxis.X
            );

            expect(mirroredPoints).toEqual([
                { x: 5, y: 2 },
                { x: 3, y: 4 },
                { x: 1, y: 6 },
            ]);
        });

        it('mirror points across the Y axis', () => {
            const mirroredPoints = mirrorPointsAcrossAxis(
                [
                    { x: 1, y: 2 },
                    { x: 3, y: 4 },
                    { x: 5, y: 6 },
                ],
                PointAxis.Y
            );

            expect(mirroredPoints).toEqual([
                { x: 1, y: 6 },
                { x: 3, y: 4 },
                { x: 5, y: 2 },
            ]);
        });
    });

    describe('getDirection', () => {
        it('SouthEast when endPoint is below and to the right of startPoint', () => {
            const startPoint = { x: 0, y: 0 };
            const endPoint = { x: 10, y: 10 };
            expect(getDirection(startPoint, endPoint)).toBe(CursorDirection.SouthEast);
        });

        it('SouthWest when endPoint is below and to the left of startPoint', () => {
            const startPoint = { x: 10, y: 0 };
            const endPoint = { x: 0, y: 10 };
            expect(getDirection(startPoint, endPoint)).toBe(CursorDirection.SouthWest);
        });

        it('NorthEast when endPoint is above and to the right of startPoint', () => {
            const startPoint = { x: 0, y: 10 };
            const endPoint = { x: 10, y: 0 };
            expect(getDirection(startPoint, endPoint)).toBe(CursorDirection.NorthEast);
        });

        it('NorthWest when endPoint is above and to the left of startPoint', () => {
            const startPoint = { x: 10, y: 10 };
            const endPoint = { x: 0, y: 0 };
            expect(getDirection(startPoint, endPoint)).toBe(CursorDirection.NorthWest);
        });
    });

    describe('getTemplateWithDirection', () => {
        const templatePoints = [
            getMockedKeypointNode({ x: 10, y: 20 }),
            getMockedKeypointNode({ x: 30, y: 10 }),
            getMockedKeypointNode({ x: 50, y: 20 }),
        ];

        it('mirrors points across the X axis for SouthWest direction', () => {
            expect(getTemplateWithDirection(templatePoints, CursorDirection.SouthWest)).toEqual([
                expect.objectContaining({ x: 50, y: 20 }),
                expect.objectContaining({ x: 30, y: 10 }),
                expect.objectContaining({ x: 10, y: 20 }),
            ]);
        });

        it('mirrors points across the Y axis for NorthEast direction', () => {
            expect(getTemplateWithDirection(templatePoints, CursorDirection.NorthEast)).toEqual([
                expect.objectContaining({ x: 10, y: 10 }),
                expect.objectContaining({ x: 30, y: 20 }),
                expect.objectContaining({ x: 50, y: 10 }),
            ]);
        });

        it('mirrors points across both axes for NorthWest direction', () => {
            expect(getTemplateWithDirection(templatePoints, CursorDirection.NorthWest)).toEqual([
                expect.objectContaining({ x: 50, y: 10 }),
                expect.objectContaining({ x: 30, y: 20 }),
                expect.objectContaining({ x: 10, y: 10 }),
            ]);
        });

        it('returns the original template points for SouthEast direction', () => {
            expect(getTemplateWithDirection(templatePoints, CursorDirection.SouthEast)).toEqual(templatePoints);
        });
    });

    describe('getPoseLocations', () => {
        const mockPoints = [
            getMockedKeypointNode({ x: 10, y: 10 }),
            getMockedKeypointNode({ x: 20, y: 10 }),
            getMockedKeypointNode({ x: 10, y: 20 }),
            getMockedKeypointNode({ x: 20, y: 20 }),
        ];

        it('calculate top, bottom, middle, and topWithGap correctly', () => {
            const gap = 5;
            const result = getPoseLocations(mockPoints, gap);

            expect(result.top).toEqual({ x: 10, y: 10 });
            expect(result.bottom).toEqual({ x: 20, y: 20 });
            expect(result.middle).toEqual({ x: 15, y: 15 });
            expect(result.topWithGap).toEqual({ x: 10, y: 0 });
        });

        it('handle a single point correctly', () => {
            const gap = 5;
            const result = getPoseLocations([getMockedKeypointNode({ x: 10, y: 10 })], gap);

            expect(result.top).toEqual({ x: 10, y: 10 });
            expect(result.bottom).toEqual({ x: 10, y: 10 });
            expect(result.middle).toEqual({ x: 10, y: 10 });
            expect(result.topWithGap).toEqual({ x: 10, y: 0 });
        });

        it('handle empty points array', () => {
            const gap = 5;
            const result = getPoseLocations([], gap);

            expect(result.top).toEqual({ x: Infinity, y: Infinity });
            expect(result.bottom).toEqual({ x: -Infinity, y: -Infinity });
            expect(result.middle).toEqual({ x: NaN, y: NaN });
            expect(result.topWithGap).toEqual({ x: Infinity, y: Infinity });
        });
    });
    describe('rotatePointsAroundPivot', () => {
        it('rotates points around the center by 90 degrees', () => {
            const points = [
                { x: 0, y: 0 },
                { x: 10, y: 0 },
                { x: 0, y: 10 },
                { x: 10, y: 10 },
            ];
            const center = { x: 5, y: 5 };
            const rotatedPoints = rotatePointsAroundPivot(points, center, 90);

            expect(rotatedPoints).toEqual([
                { x: 10, y: 0 },
                { x: 10, y: 10 },
                { x: 0, y: 0 },
                { x: 0, y: 10 },
            ]);
        });

        it('returns the same points when rotated by 0 degrees', () => {
            const points = [
                { x: 1, y: 1 },
                { x: -1, y: -1 },
            ];
            const center = { x: 0, y: 0 };
            const rotatedPoints = rotatePointsAroundPivot(points, center, 0);

            expect(rotatedPoints).toEqual(points);
        });
    });
});
