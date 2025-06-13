// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import type OpenCVTypes from 'OpenCVTypes';

import { Point, Polygon } from '../shared/interfaces';

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

export const concatFloat32Arrays = (arrays: Float32Array[]) => {
    const totalLength = arrays.reduce((c, a) => c + a.length, 0);
    const result = new Float32Array(totalLength);

    arrays.reduce((offset, array) => {
        result.set(array, offset);
        return offset + array.length;
    }, 0);

    return result;
};

export const loadSource = async (source: string, cacheKey = 'general'): Promise<Response | undefined> => {
    if (!caches) {
        return await self.fetch(source);
    }

    const cache = await caches.open(cacheKey);

    if (!(await cache.match(source))) {
        await cache.put(source, await self.fetch(source));
    }

    return cache.match(source);
};

export const stackPlanes = (CV: OpenCVTypes.cv, mat: OpenCVTypes.Mat) => {
    let stackedPlanes: OpenCVTypes.Mat[] = [];
    let matPlanes: OpenCVTypes.MatVector | null = null;

    try {
        matPlanes = new CV.MatVector();
        CV.split(mat, matPlanes);

        stackedPlanes = Array.from(Array(mat.channels()).keys()).map((index) => {
            // This won't happen, but matPlanes is mutable for the finally block.
            if (!matPlanes) {
                throw 'Lost track of matPlanes through loop';
            }

            return matPlanes.get(index);
        });

        return concatFloat32Arrays(stackedPlanes.map((m) => m.data32F));
    } finally {
        stackedPlanes.map((p) => p.delete());
        matPlanes?.delete();
    }
};

export const isPolygonValid = (polygon: Polygon | null): boolean => {
    const MINIMUM_POLYGON_AREA = 4;

    if (!polygon) return false;

    const points = polygon.points;
    if (points.length < 3) return false;

    let area = 0;
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
        area += (points[j].x + points[i].x) * (points[j].y - points[i].y);
    }

    area = Math.abs(area / 2);

    return area > MINIMUM_POLYGON_AREA;
};
