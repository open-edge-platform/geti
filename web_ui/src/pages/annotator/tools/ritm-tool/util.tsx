// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { clampBox, pointsToRect } from '../../../../core/annotations/math';
import * as Vec2 from '../../../../core/annotations/vec2';
import { RITMPoint } from './ritm-tool.interface';

export const createBoxOfMaxSize = (
    { width, height }: { width: number; height: number },
    maxSize: number
): { width: number; height: number } => {
    const scale = Math.max(width, height) / maxSize;
    return { width: (width / scale) | 0, height: (height / scale) | 0 };
};

export const scaleRegionOfInterest = ({ x, y, width, height }: RegionOfInterest, factor: number) => {
    const offset = {
        x: width * (1 - factor),
        y: height * (1 - factor),
    };

    return {
        x: x + offset.x / 2,
        y: y + offset.y / 2,
        width: width * factor,
        height: height * factor,
    };
};

export const encapsulateRegions = (regions: RegionOfInterest[]): RegionOfInterest => {
    return regions.reduce((collector, region) => {
        const x1 = Math.min(collector.x, region.x);
        const y1 = Math.min(collector.y, region.y);
        const x2 = Math.max(collector.x + collector.width, region.x + region.width);
        const y2 = Math.max(collector.y + collector.height, region.y + region.height);

        return {
            x: x1,
            y: y1,
            width: x2 - x1,
            height: y2 - y1,
        };
    });
};

export const encapsulatePoints = (points: RITMPoint[], margin: number): RegionOfInterest => {
    const boundaries = points.reduce(
        ({ topLeft, bottomRight }, point) => {
            return {
                topLeft: {
                    x: Math.min(topLeft.x, point.x),
                    y: Math.min(topLeft.y, point.y),
                },
                bottomRight: {
                    x: Math.max(bottomRight.x, point.x),
                    y: Math.max(bottomRight.y, point.y),
                },
            };
        },
        { topLeft: { x: Infinity, y: Infinity }, bottomRight: { x: 0, y: 0 } }
    );

    return pointsToRect(Vec2.subScalar(boundaries.topLeft, margin), Vec2.addScalar(boundaries.bottomRight, margin));
};

export const buildDynamicBox = (
    points: RITMPoint[],
    currentPosition: Vec2.Vec2,
    box: RegionOfInterest,
    roi: RegionOfInterest,
    margin: number
): RegionOfInterest => {
    const currentPoints = [...points, { ...currentPosition, positive: false }];
    return clampBox(encapsulateRegions([encapsulatePoints(currentPoints, margin), box]), roi);
};
