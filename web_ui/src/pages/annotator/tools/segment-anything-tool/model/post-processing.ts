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

import type cv from 'OpenCVTypes';

import { Circle, Point, Polygon, Rect, RotatedRect, Shape } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { approximateShape } from '../../../../../webworkers/utils';
import type { SegmentAnythingResult } from './segment-anything-result';

interface PostProcessorConfig {
    type: ShapeType;
    shapeFilter?: (shape: Shape) => boolean;
}

type Sizes = {
    width: number;
    height: number;
    originalWidth: number;
    originalHeight: number;
};

type ScaleToSize = {
    scaleX: (x: number) => number;
    scaleY: (x: number) => number;
};

export class PostProcessor {
    // @ts-expect-error Ignore cannot use namespace as type
    constructor(private cv: CV) {}

    public maskToAnnotationShape(
        pixels: Uint8ClampedArray,
        sizes: Sizes,
        config: PostProcessorConfig
    ): SegmentAnythingResult {
        const scales = this.scaleToOriginalSize(sizes);
        const width = sizes.width;
        const height = sizes.height;
        const mat = this.cv.matFromArray(height, width, this.cv.CV_8U, pixels);

        const contours = new this.cv.MatVector();
        const hierachy: cv.Mat = new this.cv.Mat();

        this.cv.findContours(mat, contours, hierachy, this.cv.RETR_EXTERNAL, this.cv.CHAIN_APPROX_NONE);

        let maxContourIdx = 0;
        let maxArea = -1;

        const shapes: Shape[] = [];
        const areas: number[] = [];
        const imageArea = sizes.originalWidth * sizes.originalHeight;
        for (let idx = 0; idx < Number(contours.size()); idx++) {
            const contour = contours.get(idx);
            const optimizedContour = approximateShape(this.cv, contour);
            const area = this.cv.contourArea(optimizedContour, false);

            const shape = this.contourToShape(optimizedContour, config, scales);

            // Get rid of results that might take up the whole image
            const boundingBox = this.contourToRectangle(optimizedContour, scales);
            if ((boundingBox.width * boundingBox.height) / imageArea < 0.9) {
                if (config.shapeFilter === undefined || config.shapeFilter(shape)) {
                    shapes.push(shape);
                    areas.push(area);
                    if (area > maxArea) {
                        maxArea = area;
                        maxContourIdx = shapes.length - 1;
                    }
                }
            }

            optimizedContour?.delete();
            contour?.delete();
        }

        contours.delete();
        hierachy.delete();
        mat.delete();

        // TODO: filter contours based on size (i.e. larger than x%, smaller than 90% of image)
        // TODO: give some kind of score based on area and if the points are
        // (not) included in the contour

        return { areas, maxContourIdx, shapes };
    }

    private contourToShape = (optimizedContour: cv.Mat, config: PostProcessorConfig, scales: ScaleToSize): Shape => {
        switch (config.type) {
            case ShapeType.Polygon:
                return this.contourToPolygon(optimizedContour, scales);
            case ShapeType.Rect:
                return this.contourToRectangle(optimizedContour, scales);
            case ShapeType.RotatedRect:
                return this.contourToRotatedRectangle(optimizedContour, scales);
            case ShapeType.Circle:
                return this.contourToCircle(optimizedContour, scales);
            case ShapeType.Pose:
                throw new Error('Can not create keypoint using SAM');
        }
    };

    private contourToPolygon(optimizedContour: cv.Mat, { scaleX, scaleY }: ScaleToSize): Polygon {
        const points: Point[] = [];

        for (let row = 0; row < optimizedContour.rows; row++) {
            const x = scaleX(optimizedContour.intAt(row, 0));
            const y = scaleY(optimizedContour.intAt(row, 1));

            points.push({ x, y });
        }

        return { shapeType: ShapeType.Polygon, points };
    }

    private contourToRectangle(optimizedContour: cv.Mat, { scaleX, scaleY }: ScaleToSize): Rect {
        const { x, y, width, height } = this.cv.boundingRect(optimizedContour);

        return {
            shapeType: ShapeType.Rect,
            x: scaleX(x),
            y: scaleY(y),
            width: scaleX(width),
            height: scaleY(height),
        };
    }

    private contourToRotatedRectangle(optimizedContour: cv.Mat, { scaleX, scaleY }: ScaleToSize): RotatedRect {
        const {
            angle,
            center: { x, y },
            size: { width, height },
        } = this.cv.minAreaRect(optimizedContour);

        return {
            shapeType: ShapeType.RotatedRect,
            x: scaleX(x),
            y: scaleY(y),
            width: scaleX(width),
            height: scaleY(height),
            angle,
        };
    }

    private contourToCircle(optimizedContour: cv.Mat, { scaleX, scaleY }: ScaleToSize): Circle {
        const {
            center: { x, y },
            size: { width, height },
        } = this.cv.minAreaRect(optimizedContour);

        return {
            shapeType: ShapeType.Circle,
            x: scaleX(x),
            y: scaleY(y),
            r: Math.round(Math.max(scaleX(width), scaleY(height))),
        };
    }

    private scaleToOriginalSize(sizes: Sizes): ScaleToSize {
        const { width, height, originalWidth, originalHeight } = sizes;

        return {
            scaleX: (x: number) => Math.round((x * originalWidth) / width),
            scaleY: (y: number) => Math.round((y * originalHeight) / height),
        };
    }
}
