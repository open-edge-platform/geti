// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
