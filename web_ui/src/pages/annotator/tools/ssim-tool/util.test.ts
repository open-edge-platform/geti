// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Rect, Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { SSIMMatch } from './ssim-tool.interface';
import { convertRectToShape, convertToRect, filterSSIMResults } from './util';

describe('util', () => {
    describe('filterSSIMResults', () => {
        const roi = {
            x: 0,
            y: 0,
            width: 100,
            height: 100,
        };
        it('filters nearby rects using iou', () => {
            const size = { width: 50, height: 50 };
            const template: Rect = { shapeType: ShapeType.Rect, x: 0, y: 0, ...size };
            const matches: SSIMMatch[] = [
                { shape: { shapeType: ShapeType.Rect, x: 1, y: 0, ...size }, confidence: 1 },
                { shape: { shapeType: ShapeType.Rect, x: 20, y: 50, ...size }, confidence: 1 },
            ];
            expect(filterSSIMResults(roi, matches, template, [], 0.5)).toEqual([
                { shape: { shapeType: ShapeType.Rect, x: 0, y: 0, ...size }, confidence: 1 },
                { shape: { shapeType: ShapeType.Rect, x: 20, y: 50, ...size }, confidence: 1 },
            ]);
        });

        it('always accepts user given template', () => {
            const size = { width: 50, height: 50 };
            const template: Rect = { shapeType: ShapeType.Rect, x: 0, y: 0, ...size };
            const matches: SSIMMatch[] = [{ shape: { shapeType: ShapeType.Rect, x: 1, y: 0, ...size }, confidence: 1 }];
            expect(filterSSIMResults(roi, matches, template, [])).toEqual([
                { shape: { shapeType: ShapeType.Rect, x: 0, y: 0, ...size }, confidence: 1 },
            ]);
        });

        it('also checks separate stack of rects (for existing annotations)', () => {
            const size = { width: 50, height: 50 };
            const template: Rect = { shapeType: ShapeType.Rect, x: 80, y: 50, ...size };
            const matches: SSIMMatch[] = [
                { shape: { shapeType: ShapeType.Rect, x: 1, y: 0, ...size }, confidence: 1 },
                { shape: { shapeType: ShapeType.Rect, x: 20, y: 50, ...size }, confidence: 1 },
            ];
            const existingAnnotations: Rect[] = [{ shapeType: ShapeType.Rect, x: 0, y: 0, ...size }];
            expect(filterSSIMResults(roi, matches, template, existingAnnotations)).toEqual([
                { shape: { shapeType: ShapeType.Rect, x: 80, y: 50, ...size }, confidence: 1 },
                { shape: { shapeType: ShapeType.Rect, x: 20, y: 50, ...size }, confidence: 1 },
            ]);
        });
        it('returns up to maxItems amount of results', () => {
            const size = { width: 50, height: 50 };
            const template: Rect = { shapeType: ShapeType.Rect, x: 1, y: 0, ...size };
            const matches: SSIMMatch[] = [
                { shape: { shapeType: ShapeType.Rect, x: 50, y: 30, ...size }, confidence: 1 },
                { shape: { shapeType: ShapeType.Rect, x: 10, y: 20, ...size }, confidence: 1 },
                { shape: { shapeType: ShapeType.Rect, x: 20, y: 50, ...size }, confidence: 1 },
                { shape: { shapeType: ShapeType.Rect, x: 100, y: 200, ...size }, confidence: 1 },
            ];
            expect(filterSSIMResults(roi, matches, template, [], 2)).toHaveLength(2);
        });

        it('filters items off the roi', () => {
            const size = { width: 50, height: 50 };
            const template: Rect = { shapeType: ShapeType.Rect, x: 0, y: 0, ...size };

            const valid: SSIMMatch = { shape: { shapeType: ShapeType.Rect, x: 0, y: 0, ...size }, confidence: 1 };
            const invalid: SSIMMatch = { shape: { shapeType: ShapeType.Rect, x: 60, y: 50, ...size }, confidence: 1 };
            const matches: SSIMMatch[] = [valid, invalid];

            expect(filterSSIMResults(roi, matches, template, [], 0.5)).toEqual([valid]);
        });
    });

    describe('convertToRect', () => {
        const cases: [Shape, Rect][] = [
            [
                { shapeType: ShapeType.Rect, x: 0, y: 0, width: 50, height: 50 },
                { shapeType: ShapeType.Rect, x: 0, y: 0, width: 50, height: 50 },
            ],
            [
                { shapeType: ShapeType.Circle, x: 25, y: 25, r: 25 },
                { shapeType: ShapeType.Rect, x: 0, y: 0, width: 50, height: 50 },
            ],
        ];
        test.each(cases)('converts shape %o to rect', (shape: Shape, expectedResult: Rect) => {
            expect(convertToRect(shape)).toEqual(expectedResult);
        });
    });

    describe('convertRectToShape', () => {
        const cases: [Rect, ShapeType, Shape][] = [
            [
                { shapeType: ShapeType.Rect, x: 0, y: 0, width: 50, height: 50 },
                ShapeType.Rect,
                { shapeType: ShapeType.Rect, x: 0, y: 0, width: 50, height: 50 },
            ],
            [
                { shapeType: ShapeType.Rect, x: 0, y: 0, width: 50, height: 50 },
                ShapeType.Circle,
                { shapeType: ShapeType.Circle, x: 25, y: 25, r: 25 },
            ],
        ];
        test.each(cases)('converts shape %o to rect', (shape: Rect, shapeType: ShapeType, expectedResult: Shape) => {
            expect(convertRectToShape(shape, shapeType)).toEqual(expectedResult);
        });
    });
});
