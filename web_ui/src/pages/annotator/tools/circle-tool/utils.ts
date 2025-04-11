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
