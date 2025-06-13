// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// Dependencies get bundled into the worker

import { OpenCVLoader } from '@geti/smart-tools';
import { expose } from 'comlink';
import type OpenCVTypes from 'OpenCVTypes';

import { Point, Polygon } from '../core/annotations/shapes.interface';
import { ShapeType } from '../core/annotations/shapetype.enum';
import { isPointOutsideOfBounds, optimizePolygonAndCV } from './utils';

declare const self: DedicatedWorkerGlobalScope;

let CV: OpenCVTypes.cv | null = null;

const terminate = (): void => {
    self.close();
};

interface IntelligentScissorsMB {
    setGradientMagnitudeMaxLimit: (gradient_magnitude_threshold_max: number) => void;
    setEdgeFeatureCannyParameters: (threshold1: number, threshold2: number) => void;
    applyImage: (image: OpenCVTypes.Mat) => void;
    buildMap: (sourcePt: Point) => void;
    getContour: (targetPt: Point, contour: OpenCVTypes.Mat, backward?: boolean) => void;
}

const maxRoiSize = 600;
class IntelligentScissors {
    img: OpenCVTypes.Mat;
    tool: IntelligentScissorsMB;
    hasInitialPoint: boolean;
    roiRect: OpenCVTypes.Rect | null;

    constructor(imageData: ImageData) {
        this.roiRect = null;
        this.hasInitialPoint = false;
        this.tool = new CV.segmentation_IntelligentScissorsMB();
        this.tool.setGradientMagnitudeMaxLimit(200);
        this.tool.setEdgeFeatureCannyParameters(16, 100);
        this.img = CV.matFromImageData(imageData) as OpenCVTypes.Mat;
    }

    buildMap(point: Point): void {
        this.hasInitialPoint = true;

        const { roiRect, roiImg } = this.getRoiAndCrop(this.img, point, maxRoiSize);
        this.roiRect = roiRect;

        try {
            this.tool.applyImage(roiImg);
            this.tool.buildMap(this.getRelativePoint(this.roiRect, point));
        } finally {
            roiImg?.delete();
        }
    }

    calcPoints(point: Point): Point[] {
        if (!this.hasInitialPoint) {
            return [];
        }

        const relativePoint = this.getRelativePoint(this.roiRect, point);
        const realLimit = this.getRelativeLimit(this.img, this.roiRect);

        if (isPointOutsideOfBounds(realLimit, relativePoint)) {
            return [];
        }

        const contour = new CV.Mat();
        try {
            this.tool.getContour(relativePoint, contour);
            return this.formatContourToPoints(contour, this.roiRect);
        } finally {
            contour?.delete();
        }
    }

    getRoiAndCrop(
        src: OpenCVTypes.Mat,
        point: Point,
        roiSize: number
    ): { roiRect: OpenCVTypes.Rect | null; roiImg: OpenCVTypes.Mat } {
        if (src.cols > roiSize) {
            const roiRect = this.getRoiRect(this.img, point, maxRoiSize);
            const roiImg = this.cropArea(this.img, roiRect);

            return { roiRect, roiImg };
        }

        return { roiRect: null, roiImg: src.clone() };
    }

    getRoiRect(src: OpenCVTypes.Mat, point: Point, roiSize: number): OpenCVTypes.Rect {
        const finalRioSize = roiSize / 2;
        const x = Math.round(Math.max(0, point.x - finalRioSize));
        const y = Math.round(Math.max(0, point.y - finalRioSize));
        const width = roiSize + x > src.cols ? src.cols - x : roiSize;
        const height = roiSize + y > src.rows ? src.rows - y : roiSize;

        return new CV.Rect(x, y, width, height);
    }

    cropArea(src: OpenCVTypes.Mat, rect: OpenCVTypes.Rect): OpenCVTypes.Mat {
        let dst = new CV.Mat();
        dst = src.roi(rect);

        return dst;
    }

    formatContourToPoints(contour: OpenCVTypes.Mat, rectOffset: OpenCVTypes.Rect | null): Point[] {
        const points: Point[] = [];
        const { x: offsetX, y: offsetY } = rectOffset ?? { x: 0, y: 0 };
        for (let row = 0; row < contour.rows; row++) {
            points.push({
                x: Math.round(contour.intAt(row, 0) + offsetX),
                y: Math.round(contour.intAt(row, 1) + offsetY),
            });
        }

        return points;
    }

    getRelativePoint(roiRect: OpenCVTypes.Rect | null, point: Point): OpenCVTypes.Point {
        if (roiRect === null) {
            return new CV.Point(point.x, point.y);
        }
        return new CV.Point(point.x - roiRect.x, point.y - roiRect.y);
    }

    getRelativeLimit(
        src: OpenCVTypes.Mat,
        roiRect: OpenCVTypes.Rect | null
    ): { x: number; y: number; width: number; height: number } {
        return {
            x: 0,
            y: 0,
            width: roiRect ? roiRect.width : src.cols,
            height: roiRect ? roiRect.height : src.rows,
        };
    }

    cleanPoints(): void {
        this.hasInitialPoint = false;
    }

    cleanImg(): void {
        this.img?.delete();
        this.roiRect = null;
    }
}

const waitForOpenCV = async (): Promise<boolean> => {
    if (CV) {
        return true;
    } else {
        return OpenCVLoader().then((cvInstance: OpenCVTypes.cv) => {
            CV = cvInstance;

            return true;
        });
    }
};

const optimizePolygon = (prevPolygon: Polygon): Polygon => {
    return { ...prevPolygon, points: optimizePolygonAndCV(CV, prevPolygon.points) };
};

const optimizeSegments = (segments: Point[][]): Polygon => {
    const optimizeOrReturnSegment = (segment: Point[]) =>
        segment.length > 1 ? optimizePolygonAndCV(CV, segment, false) : segment;

    const points = segments.map(optimizeOrReturnSegment).flat();

    return { shapeType: ShapeType.Polygon, points };
};

const WorkerApi = { IntelligentScissors, waitForOpenCV, optimizePolygon, optimizeSegments, terminate };

expose(WorkerApi);
