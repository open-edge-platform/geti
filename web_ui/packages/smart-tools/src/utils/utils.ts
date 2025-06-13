// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import type OpenCVTypes from 'OpenCVTypes';

import { Point } from '../shared/interfaces';

export const formatContourToPoints = (
    mask: OpenCVTypes.Mat,
    contour: OpenCVTypes.Mat,
    width: number,
    height: number
): Point[] => {
    const points: Point[] = [];

    if (!contour?.rows) {
        return points;
    }

    for (let row = 0; row < contour.rows; row++) {
        points.push({
            x: (contour.intAt(row, 0) / mask.cols) * width,
            y: (contour.intAt(row, 1) / mask.rows) * height,
        });
    }

    return points;
};

// It approximates a contour shape to another shape with less number of vertices
export const approximateShape = (CV: OpenCVTypes.cv, contour: OpenCVTypes.Mat, isClose = true): OpenCVTypes.Mat => {
    const epsilon = 1.0;
    const newContour = new CV.Mat();

    CV.approxPolyDP(contour, newContour, epsilon, isClose);

    return newContour;
};
