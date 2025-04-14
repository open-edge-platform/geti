// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { calculateDistance } from '../../../../core/annotations/math';
import { Circle, Point } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';

export enum Mode {
    NORMAL,
    EDIT_RADIUS,
}

export const pointsToCircle = (startPoint: Point, endPoint: Point, minRadius: number): Circle => {
    const radius = Math.round(calculateDistance(startPoint, endPoint));

    return {
        x: startPoint.x,
        y: startPoint.y,
        r: radius <= minRadius ? minRadius : radius,
        shapeType: ShapeType.Circle,
    };
};

export const MIN_RADIUS = 1;

export const getMaxCircleRadius = (roi: RegionOfInterest): number => {
    return Math.round(Math.max(roi.width / 2, roi.height / 2));
};
