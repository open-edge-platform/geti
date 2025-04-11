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

import { Point } from '../../../core/annotations/shapes.interface';

const DEFAULT_SCREEN_ZOOM = 0.85;

interface Container {
    width: number;
    height: number;
}

export const getCenterCoordinates = (container: Container, target: Point & Container) => {
    const scale = DEFAULT_SCREEN_ZOOM * Math.min(container.width / target.width, container.height / target.height);

    // Center the target in the middle of the container
    const centerOffsetX = (container.width - scale * target.width) / 2;
    const centerOffsetY = (container.height - scale * target.height) / 2;
    const x = -scale * target.x + centerOffsetX;
    const y = -scale * target.y + centerOffsetY;

    return { x, y, scale };
};
