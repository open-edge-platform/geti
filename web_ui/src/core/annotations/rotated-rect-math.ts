// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { rotateDeg } from './math';
import { Rect, RotatedRect } from './shapes.interface';
import { ShapeType } from './shapetype.enum';
import * as Vec2 from './vec2';

export const transformPointInRotatedRectToScreenSpace = (position: Vec2.Vec2, shape: RotatedRect): Vec2.Vec2 => {
    const shapePosition = { x: shape.x, y: shape.y };
    const temp = Vec2.sub(position, shapePosition);
    const rotated = rotateDeg(temp, shape.angle);
    return Vec2.add(rotated, shapePosition);
};

export const calculateSizeAndPositionBasedOfCornerAnchor = (
    position: Vec2.Vec2,
    corner: Vec2.Vec2,
    oppositeCorner: Vec2.Vec2,
    shape: RotatedRect,
    gap: number
): { x: number; y: number; width: number; height: number } => {
    const size = rotateDeg(Vec2.sub(oppositeCorner, position), -shape.angle);
    const sign = Vec2.sign(rotateDeg(Vec2.sub(oppositeCorner, corner), -shape.angle));
    const dimensions = Vec2.mul(sign, size);
    const constrainedDimensions = {
        x: Math.max(dimensions.x, gap),
        y: Math.max(dimensions.y, gap),
    };
    const constrainedPosition = Vec2.sub(oppositeCorner, rotateDeg(Vec2.mul(constrainedDimensions, sign), shape.angle));

    return {
        ...Vec2.divScalar(Vec2.add(oppositeCorner, constrainedPosition), 2),
        width: constrainedDimensions.x,
        height: constrainedDimensions.y,
    };
};

export const calculateSizeAndPositionOfSideAnchor = (
    position: Vec2.Vec2,
    side: Vec2.Vec2,
    opposite: Vec2.Vec2,
    gap: number
): { x: number; y: number; size: number } => {
    const movement = Vec2.sub(position, side);
    const centerNorm = Vec2.normalize(Vec2.sub(opposite, side));
    const alongAxis = Vec2.mulScalar(centerNorm, Vec2.dot(centerNorm, movement));
    const alignedPosition = Vec2.add(alongAxis, side);
    const size = Vec2.sub(opposite, alignedPosition);
    const constrainedSize = Vec2.mulScalar(Vec2.normalize(size), Math.max(gap, Vec2.magnitude(size)));
    const constrainedPosition = Vec2.sub(opposite, Vec2.divScalar(constrainedSize, 2));
    // TODO: Fix the shifting when going too far below.
    return {
        ...constrainedPosition,
        size: Vec2.magnitude(constrainedSize),
    };
};

export const cursorForDirection = (position_a: Vec2.Vec2, position_b: Vec2.Vec2): string => {
    const angle = (Vec2.getAngleDegrees(Vec2.sub(position_b, position_a)) + 360) % 360;
    const cursorIndex = Math.round(angle / 45) % 8;
    const cursor = ['w', 'nw', 'n', 'ne', 'e', 'se', 's', 'sw'];
    return `${cursor[cursorIndex]}-resize`;
};

export const rectToRotatedRect = (shape: Rect): RotatedRect => {
    return {
        ...shape,
        x: shape.x + shape.width / 2,
        y: shape.y + shape.height / 2,
        shapeType: ShapeType.RotatedRect,
        angle: 0,
    };
};
