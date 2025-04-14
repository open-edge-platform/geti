// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import polylabel from 'polylabel';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { highestCorner, lowestCorner } from '../../../../core/annotations/math';
import { isCircle, isPolygon, isPoseShape, isRect, isRotatedRect } from '../../../../core/annotations/utils';

const getShapeHeight = (annotation: Annotation) => {
    if (isCircle(annotation.shape)) {
        return annotation.shape.r * 2;
    }

    if (isRect(annotation.shape)) {
        return annotation.shape.height;
    }

    if (isRotatedRect(annotation.shape)) {
        return lowestCorner(annotation.shape).y - highestCorner(annotation.shape).y;
    }

    return 0;
};

export const useLabelPosition = (annotation: Annotation) => {
    return useMemo(() => {
        if (isPolygon(annotation.shape)) {
            const { points } = annotation.shape;
            const axisY = points.map((point) => point.y);
            const [x, y] = polylabel([points.map((point) => [point.x, point.y])]);
            const [top, bottom] = [Math.min(...axisY), Math.max(...axisY)];

            return { x, y, height: bottom - top };
        }
        // TODO: Added to meet TS requirements,
        // we don't render labels per annotation but by point
        if (isPoseShape(annotation.shape)) {
            return {
                x: 0,
                y: 0,
                height: getShapeHeight(annotation),
            };
        }

        return {
            x: annotation.shape.x,
            y: annotation.shape.y,
            height: getShapeHeight(annotation),
        };
    }, [annotation]);
};
