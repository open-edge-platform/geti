// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeypointNode } from '../../../../../core/annotations/shapes.interface';

export const updatePoint = (points: KeypointNode[], index: number, newPoint: Partial<KeypointNode>) => {
    return points.map((currentPoint, currentIdx) =>
        index === currentIdx ? { ...currentPoint, ...newPoint } : { ...currentPoint }
    );
};

export const toggleVisibility = (points: KeypointNode[], index: number) => {
    return updatePoint(points, index, { isVisible: !points[index].isVisible });
};
