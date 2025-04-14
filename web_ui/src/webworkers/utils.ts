// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import OpenCVTypes from 'OpenCVTypes';

import { Point } from '../core/annotations/shapes.interface';

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

export const isPointOutsideOfBounds = (limit: OpenCVTypes.Rect, point: OpenCVTypes.Point | Point): boolean =>
    point.x <= limit.x || point.x >= limit.width || point.y <= limit.y || point.y >= limit.height;

export const optimizePolygonAndCV = (CV: OpenCVTypes.cv, points: Point[], isClose = true): Point[] => {
    const pointsMat = getMatFromPoints(CV, points);
    const newContour = approximateShape(CV, pointsMat, isClose);
    pointsMat.delete();

    const newPoints = getPointsFromMat(newContour);
    newContour.delete();

    return newPoints;
};

//It approximates a contour shape to another shape with less number of vertices
export const approximateShape = (CV: OpenCVTypes.cv, contour: OpenCVTypes.Mat, isClose = true): OpenCVTypes.Mat => {
    const epsilon = 1.0;
    const newContour = new CV.Mat();

    CV.approxPolyDP(contour, newContour, epsilon, isClose);

    return newContour;
};

export const getMatFromPoints = (CV: OpenCVTypes.cv, points: Point[], offset = { x: 0, y: 0 }): OpenCVTypes.Mat => {
    const pointsMat = new CV.Mat(points.length, 1, CV.CV_32SC2);

    points.forEach(({ x, y }, idx) => {
        pointsMat.intPtr(idx, 0)[0] = x + offset.x;
        pointsMat.intPtr(idx, 0)[1] = y + offset.y;
    });

    return pointsMat;
};

export const getPointsFromMat = (mat: OpenCVTypes.Mat, offset = { x: 0, y: 0 }): Point[] => {
    const points: Point[] = [];

    for (let row = 0; row < mat.rows; row++) {
        points.push({
            x: Math.round(mat.intAt(row, 0) + offset.x),
            y: Math.round(mat.intAt(row, 1) + offset.y),
        });
    }
    return points;
};

export const formatImageData = (CV: OpenCVTypes.cv, mat: OpenCVTypes.Mat): ImageData => {
    const img = new CV.Mat();
    const depth = mat.type() % 8;
    const scale = depth <= CV.CV_8S ? 1 : depth <= CV.CV_32S ? 1 / 256 : 255;
    const shift = depth === CV.CV_8S || depth === CV.CV_16S ? 128 : 0;

    mat.convertTo(img, CV.CV_8U, scale, shift);

    switch (img.type()) {
        case CV.CV_8UC1:
            CV.cvtColor(img, img, CV.COLOR_GRAY2RGBA);
            break;
        case CV.CV_8UC3:
            CV.cvtColor(img, img, CV.COLOR_RGB2RGBA);
            break;
        case CV.CV_8UC4:
            break;
        default:
            throw new Error('Bad number of channels (Source image must have 1, 3 or 4 channels)');
    }

    return new ImageData(new Uint8ClampedArray(img.data), img.cols, img.rows);
};

// For debugging purposes, not being used atm
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const logMat = (mat: OpenCVTypes.Mat, name: string): void => {
    // eslint-disable-next-line no-console
    console.log(
        `${name} width: ${mat.cols}
        ${name} height: ${mat.rows}
        ${name} size: ${mat.size().width * mat.size().height}
        ${name} depth: ${mat.depth()}
        ${name} channels: ${mat.channels()}
        ${name} type:${mat.type()}`
    );
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

const numberFormatter = new Intl.NumberFormat('en-GB', {
    style: 'unit',
    unit: 'megabyte',
    unitDisplay: 'short',
});

// For debugging purposes, not being used atm
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const reportOpenCVMemoryUsage = (CV: OpenCVTypes.cv, message = '') => {
    const byteLength = CV.asm.memory.buffer.byteLength;

    console.info(`${message} OpenCV Memory: ${numberFormatter.format(byteLength / 1024 / 1024)}`);
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
