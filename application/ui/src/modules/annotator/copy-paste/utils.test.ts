// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getMockedAnnotation, getMockedShape } from 'mocks/mock-annotation';

import type { Polygon, Rect } from '../../../shared/types';
import { getCascadeStep, getCenterOfShape, getTranslateVector, preparePaste, toClipboardAnnotations } from './utils';

const roi = { x: 0, y: 0, width: 100, height: 100 };
const noOffset = () => ({ x: 0, y: 0 });
const validLabelIds = ['a', 'b'];

describe('getCascadeStep', () => {
    it('divides 10 screen pixels by the zoom scale', () => {
        expect(getCascadeStep(1)).toBe(10);
        expect(getCascadeStep(2)).toBe(5);
        expect(getCascadeStep(0.5)).toBe(20);
    });
});

describe('toClipboardAnnotations', () => {
    it('drops full_image annotations', () => {
        const rectangle = getMockedAnnotation({
            id: '1',
            shape: getMockedShape({ type: 'rectangle', x: 1, y: 2, width: 3, height: 4 }),
        });
        const result = toClipboardAnnotations([
            rectangle,
            getMockedAnnotation({ id: '2', shape: getMockedShape({ type: 'full_image' }) }),
        ]);

        expect(result).toEqual([rectangle]);
    });
});

describe('getTranslateVector', () => {
    it.each([
        [
            { x: 25, y: 25 },
            { x: 10, y: 10 },
        ],
        [
            { x: 75, y: 25 },
            { x: -10, y: 10 },
        ],
        [
            { x: 75, y: 75 },
            { x: -10, y: -10 },
        ],
        [
            { x: 25, y: 75 },
            { x: 10, y: -10 },
        ],
        [
            { x: 50, y: 50 },
            { x: 10, y: -10 },
        ],
    ])('translates %j toward the center', (center, expected) => {
        expect(getTranslateVector(center, 100, 100, 10)).toEqual(expected);
    });
});

describe('getCenterOfShape', () => {
    it('returns the rectangle midpoint', () => {
        expect(
            getCenterOfShape(getMockedShape({ type: 'rectangle', x: 10, y: 20, width: 40, height: 60 }) as Rect)
        ).toEqual({ x: 30, y: 50 });
    });

    it('returns an interior point for a concave polygon whose bounding-box center is outside', () => {
        const center = getCenterOfShape(
            getMockedShape({
                type: 'polygon',
                points: [
                    { x: 0, y: 0 },
                    { x: 100, y: 0 },
                    { x: 100, y: 20 },
                    { x: 20, y: 20 },
                    { x: 20, y: 100 },
                    { x: 0, y: 100 },
                ],
            }) as Polygon
        );

        expect(center.x).toBeGreaterThan(0);
        expect(center.y).toBeGreaterThan(0);
        expect(center.x < 20 || center.y < 20).toBe(true);
    });
});

describe('preparePaste', () => {
    it('returns identical shapes for a zero offset', () => {
        const clipboard = [
            getMockedAnnotation({
                id: '1',
                labels: [{ id: 'a' }],
                shape: getMockedShape({ type: 'rectangle', x: 10, y: 10, width: 20, height: 20 }),
            }),
            getMockedAnnotation({
                id: '2',
                labels: [{ id: 'a' }],
                shape: getMockedShape({
                    type: 'polygon',
                    points: [
                        { x: 0, y: 0 },
                        { x: 50, y: 0 },
                        { x: 50, y: 50 },
                    ],
                }),
            }),
        ];

        const { annotations, skipped } = preparePaste({ clipboard, validLabelIds, roi, offset: noOffset });

        expect(annotations.map(({ shape }) => shape)).toEqual(clipboard.map(({ shape }) => shape));
        expect(skipped).toEqual({ labelMissing: 0, outsideImage: 0 });
    });

    it('applies the offset to rectangles and every polygon point', () => {
        const clipboard = [
            getMockedAnnotation({
                id: '1',
                labels: [{ id: 'a' }],
                shape: getMockedShape({ type: 'rectangle', x: 10, y: 10, width: 20, height: 20 }),
            }),
            getMockedAnnotation({
                id: '2',
                labels: [{ id: 'a' }],
                shape: getMockedShape({
                    type: 'polygon',
                    points: [
                        { x: 0, y: 0 },
                        { x: 20, y: 0 },
                        { x: 20, y: 20 },
                    ],
                }),
            }),
        ];

        const { annotations } = preparePaste({ clipboard, validLabelIds, roi, offset: () => ({ x: 5, y: 7 }) });

        expect(annotations[0].shape).toEqual(
            getMockedShape({ type: 'rectangle', x: 15, y: 17, width: 20, height: 20 })
        );
        expect(annotations[1].shape).toEqual(
            getMockedShape({
                type: 'polygon',
                points: [
                    { x: 5, y: 7 },
                    { x: 25, y: 7 },
                    { x: 25, y: 27 },
                ],
            })
        );
    });

    it('does not mutate the clipboard', () => {
        const clipboard = [
            getMockedAnnotation({
                id: '1',
                labels: [{ id: 'a' }],
                shape: getMockedShape({ type: 'rectangle', x: 10, y: 10, width: 20, height: 20 }),
            }),
            getMockedAnnotation({
                id: '2',
                labels: [{ id: 'a' }],
                shape: getMockedShape({
                    type: 'polygon',
                    points: [
                        { x: 0, y: 0 },
                        { x: 20, y: 0 },
                        { x: 20, y: 20 },
                    ],
                }),
            }),
        ];
        const snapshot = structuredClone(clipboard);

        preparePaste({ clipboard, validLabelIds, roi, offset: () => ({ x: 90, y: 90 }) });

        expect(clipboard).toEqual(snapshot);
    });

    it('skips annotations with any label missing from the project', () => {
        const clipboard = [
            getMockedAnnotation({
                id: '1',
                shape: getMockedShape({ type: 'rectangle', x: 0, y: 0, width: 10, height: 10 }),
                labels: [{ id: 'a' }],
            }),
            getMockedAnnotation({
                id: '2',
                shape: getMockedShape({ type: 'rectangle', x: 0, y: 0, width: 10, height: 10 }),
                labels: [{ id: 'a' }, { id: 'deleted' }],
            }),
        ];

        const { annotations, skipped } = preparePaste({ clipboard, validLabelIds, roi, offset: noOffset });

        expect(annotations).toHaveLength(1);
        expect(annotations[0].labels).toEqual([{ id: 'a' }]);
        expect(skipped).toEqual({ labelMissing: 1, outsideImage: 0 });
    });

    describe('rectangles', () => {
        it('clips a partly overlapping rectangle to the roi', () => {
            const { annotations } = preparePaste({
                clipboard: [
                    getMockedAnnotation({
                        id: '1',
                        labels: [{ id: 'a' }],
                        shape: getMockedShape({ type: 'rectangle', x: 80, y: 90, width: 40, height: 40 }),
                    }),
                ],
                validLabelIds,
                roi,
                offset: noOffset,
            });

            expect(annotations[0].shape).toEqual(
                getMockedShape({ type: 'rectangle', x: 80, y: 90, width: 20, height: 10 })
            );
        });

        it('skips a rectangle fully outside the roi', () => {
            const { annotations, skipped } = preparePaste({
                clipboard: [
                    getMockedAnnotation({
                        id: '1',
                        labels: [{ id: 'a' }],
                        shape: getMockedShape({ type: 'rectangle', x: 10, y: 10, width: 20, height: 20 }),
                    }),
                ],
                validLabelIds,
                roi,
                offset: () => ({ x: 200, y: 200 }),
            });

            expect(annotations).toEqual([]);
            expect(skipped.outsideImage).toBe(1);
        });

        it('skips a rectangle that only touches the roi edge (zero width after clipping)', () => {
            const { annotations, skipped } = preparePaste({
                clipboard: [
                    getMockedAnnotation({
                        id: '1',
                        labels: [{ id: 'a' }],
                        shape: getMockedShape({ type: 'rectangle', x: 100, y: 10, width: 20, height: 20 }),
                    }),
                ],
                validLabelIds,
                roi,
                offset: noOffset,
            });

            expect(annotations).toEqual([]);
            expect(skipped.outsideImage).toBe(1);
        });
    });

    describe('polygons', () => {
        it('clips a partly overlapping polygon so every point is inside the roi', () => {
            const { annotations, skipped } = preparePaste({
                clipboard: [
                    getMockedAnnotation({
                        id: '1',
                        labels: [{ id: 'a' }],
                        shape: getMockedShape({
                            type: 'polygon',
                            points: [
                                { x: 80, y: 10 },
                                { x: 130, y: 10 },
                                { x: 130, y: 60 },
                                { x: 80, y: 60 },
                            ],
                        }),
                    }),
                ],
                validLabelIds,
                roi,
                offset: noOffset,
            });

            const { points } = annotations[0].shape as Polygon;

            expect(skipped.outsideImage).toBe(0);
            expect(points.length).toBeGreaterThanOrEqual(3);
            expect(points.every(({ x, y }) => x >= 0 && x <= 100 && y >= 0 && y <= 100)).toBe(true);
            expect(Math.max(...points.map(({ x }) => x))).toBe(100);
        });

        it('keeps the largest piece when clipping splits a concave polygon', () => {
            // "U" whose two arms stick out below the roi; clipping must still yield a single in-bounds polygon.
            const u = getMockedShape({
                type: 'polygon',
                points: [
                    { x: 10, y: 10 },
                    { x: 90, y: 10 },
                    { x: 90, y: 150 },
                    { x: 70, y: 150 },
                    { x: 70, y: 30 },
                    { x: 30, y: 30 },
                    { x: 30, y: 150 },
                    { x: 10, y: 150 },
                ],
            });

            const { annotations } = preparePaste({
                clipboard: [getMockedAnnotation({ id: '1', shape: u, labels: [{ id: 'a' }] })],
                validLabelIds,
                roi,
                offset: noOffset,
            });

            const { points } = annotations[0].shape as Polygon;

            expect(points.every(({ y }) => y <= 100)).toBe(true);
            expect(points.length).toBeGreaterThanOrEqual(3);
        });

        it('skips a polygon fully outside the roi', () => {
            const { annotations, skipped } = preparePaste({
                clipboard: [
                    getMockedAnnotation({
                        id: '1',
                        labels: [{ id: 'a' }],
                        shape: getMockedShape({
                            type: 'polygon',
                            points: [
                                { x: 0, y: 0 },
                                { x: 20, y: 0 },
                                { x: 20, y: 20 },
                            ],
                        }),
                    }),
                ],
                validLabelIds,
                roi,
                offset: () => ({ x: 300, y: 300 }),
            });

            expect(annotations).toEqual([]);
            expect(skipped.outsideImage).toBe(1);
        });
    });
});
