// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Rect } from './shapes.interface';

const intersect = (rectA: Rect, rectB: Rect) => {
    return (
        rectA.x <= rectB.x + rectB.width &&
        rectA.x + rectA.width >= rectB.x &&
        rectA.y <= rectB.y + rectB.height &&
        rectA.y + rectA.height >= rectB.y
    );
};

export const intersectionOverUnion = (rectA: Rect, rectB: Rect) => {
    if (!intersect(rectA, rectB)) return 0;
    const lowest = {
        x: Math.max(rectA.x, rectB.x),
        y: Math.max(rectA.y, rectB.y),
    };
    const highest = {
        x: Math.min(rectA.x + rectA.width, rectB.x + rectB.width),
        y: Math.min(rectA.y + rectA.height, rectB.y + rectB.height),
    };
    const areaOfIntersect: number = (highest.x - lowest.x) * (highest.y - lowest.y);

    return areaOfIntersect / (rectA.width * rectA.height + rectB.width * rectB.height - areaOfIntersect);
};
