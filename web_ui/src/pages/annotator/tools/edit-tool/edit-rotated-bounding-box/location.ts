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

import { transformPointInRotatedRectToScreenSpace } from '../../../../../core/annotations/rotated-rect-math';
import { Point, RotatedRect } from '../../../../../core/annotations/shapes.interface';
import * as Vec2 from '../../../../../core/annotations/vec2';

const getLocations = (shape: RotatedRect, gap: number) => {
    const top = { x: shape.x, y: shape.y - shape.height / 2 };
    const start = { x: shape.x - shape.width / 2, y: shape.y };
    const bottom = { x: shape.x, y: shape.y + shape.height / 2 };
    const end = { x: shape.x + shape.width / 2, y: shape.y };
    const middle = { x: shape.x, y: shape.y };

    return {
        top,
        bottom,
        start,
        end,
        middle,
        topWithGap: { ...top, y: top.y - gap * 2 },
        bottomWithGap: { ...bottom, y: bottom.y + gap * 2 },
        startWithGap: { ...start, x: start.x - gap * 2 },
        endWithGap: { ...end, x: end.x + gap * 2 },
    };
};

interface SideLocationsProps {
    W: Vec2.Vec2;
    E: Vec2.Vec2;
    S: Vec2.Vec2;
    N: Vec2.Vec2;
    Middle: Vec2.Vec2;
}

export interface SideAnchorLocationsProps extends SideLocationsProps {
    withGap: SideLocationsProps;
    lineEnd: Omit<SideLocationsProps, 'Middle'>;
    baseVector: {
        W: Point;
        E: Point;
        S: Point;
        N: Point;
        Middle: Point;
    };
}

export const getSideAnchorLocations = (shape: RotatedRect, gap: number): SideAnchorLocationsProps => {
    const locations = getLocations(shape, gap);

    return {
        W: transformPointInRotatedRectToScreenSpace(locations.start, shape),
        N: transformPointInRotatedRectToScreenSpace(locations.top, shape),
        E: transformPointInRotatedRectToScreenSpace(locations.end, shape),
        S: transformPointInRotatedRectToScreenSpace(locations.bottom, shape),
        Middle: transformPointInRotatedRectToScreenSpace(locations.middle, shape),
        withGap: {
            W: transformPointInRotatedRectToScreenSpace(locations.startWithGap, shape),
            N: transformPointInRotatedRectToScreenSpace(locations.topWithGap, shape),
            E: transformPointInRotatedRectToScreenSpace(locations.endWithGap, shape),
            S: transformPointInRotatedRectToScreenSpace(locations.bottomWithGap, shape),
            Middle: transformPointInRotatedRectToScreenSpace(locations.middle, shape),
        },
        lineEnd: {
            W: transformPointInRotatedRectToScreenSpace(
                { x: locations.startWithGap.x + gap / 2, y: locations.startWithGap.y },
                shape
            ),
            N: transformPointInRotatedRectToScreenSpace(
                { x: locations.topWithGap.x, y: locations.topWithGap.y + gap / 2 },
                shape
            ),
            E: transformPointInRotatedRectToScreenSpace(
                { x: locations.endWithGap.x - gap / 2, y: locations.endWithGap.y },
                shape
            ),
            S: transformPointInRotatedRectToScreenSpace(
                { x: locations.bottomWithGap.x, y: locations.bottomWithGap.y - gap / 2 },
                shape
            ),
        },
        baseVector: {
            W: { x: -1, y: 0 },
            E: { x: 1, y: 0 },
            S: { x: 0, y: 1 },
            N: { x: 0, y: -1 },
            Middle: { x: 0, y: 0 },
        },
    };
};
