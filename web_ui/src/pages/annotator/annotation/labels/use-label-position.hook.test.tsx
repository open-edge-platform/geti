// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';
import polylabel from 'polylabel';

import { Circle, Rect, RotatedRect } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { useLabelPosition } from './use-label-position.hook';

jest.mock('polylabel');

describe('useLabelPosition', () => {
    afterAll(() => {
        jest.clearAllMocks();
    });

    const rectAnnotation = getMockedAnnotation({}, ShapeType.Rect);
    const circleAnnotation = getMockedAnnotation({}, ShapeType.Circle);
    const rotatedRectAnnotation = getMockedAnnotation(
        { shape: { shapeType: ShapeType.RotatedRect, x: 0, y: 10, angle: 0, width: 100, height: 110 } },
        ShapeType.RotatedRect
    );

    it('returns shape x and y coordinates when shape type is different to Polygon', async () => {
        const { result: r1 } = renderHook(() => useLabelPosition(rectAnnotation));
        const rectShape = rectAnnotation.shape as Rect;
        expect(r1.current).toEqual({ x: rectShape.x, y: rectShape.y, height: rectShape.height });

        const { result: r2 } = renderHook(() => useLabelPosition(circleAnnotation));
        const circleShape = circleAnnotation.shape as Circle;
        expect(r2.current).toEqual({ x: circleShape.x, y: circleShape.y, height: circleShape.r * 2 });

        const { result: r3 } = renderHook(() => useLabelPosition(rotatedRectAnnotation));
        const rotatedRectShape = rectAnnotation.shape as RotatedRect;
        expect(r3.current).toEqual({ x: rotatedRectShape.x, y: rotatedRectShape.y, height: rotatedRectShape.height });
    });

    it('returns polylabel x and y for polygon shapes', async () => {
        const mockResult = [2, 4];
        // @ts-expect-error we ignore the distance field
        jest.mocked(polylabel).mockReturnValue(mockResult);

        const { result } = renderHook(() => useLabelPosition(getMockedAnnotation({}, ShapeType.Polygon)));
        const [x, y] = mockResult;
        expect(result.current).toEqual({ x, y, height: 10 });
    });
});
