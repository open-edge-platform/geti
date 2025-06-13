// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//  Dependencies get bundled into the worker

import { OpenCVLoader } from '@geti/smart-tools';
import { expose } from 'comlink';
import type OpenCVTypes from 'OpenCVTypes';

import { Point, Polygon, Rect } from '../core/annotations/shapes.interface';
import { ShapeType } from '../core/annotations/shapetype.enum';
import { GrabcutToolType } from '../pages/annotator/tools/grabcut-tool/grabcut-tool.enums';
import { GrabcutData } from '../pages/annotator/tools/grabcut-tool/grabcut-tool.interface';
import { approximateShape, getMatFromPoints, getPointsFromMat } from './utils';

declare const self: DedicatedWorkerGlobalScope;

let CV: OpenCVTypes.cv | null = null;

const terminate = (): void => {
    self.close();
};

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

interface GrabcutDependencies {
    scale: number;
    roiRect: OpenCVTypes.Rect;
    resizedImg: OpenCVTypes.Mat;
}

class Grabcut {
    img: OpenCVTypes.Mat;
    mask: OpenCVTypes.Mat;
    bgdModel: OpenCVTypes.Mat;
    fgdModel: OpenCVTypes.Mat;

    constructor(imageData: ImageData) {
        this.mask = new CV.Mat();
        this.bgdModel = new CV.Mat();
        this.fgdModel = new CV.Mat();
        this.img = this.getImage(imageData);
    }

    startGrabcut(data: GrabcutData): Polygon {
        const roiRect = this.formatRoiRect(data.inputRect);
        const scale = this.getScale(roiRect, data.sensitivity);
        const resizedImg = this.cropAndResize(this.img, roiRect, scale);
        const hasMarkers = data.foreground.length || data.background.length;
        const runGrabcut = () =>
            this.mask.matSize.length && hasMarkers
                ? this.runGrabcutMask({ ...data, roiRect, resizedImg, scale })
                : this.runGrabcutRect({ roiRect, resizedImg, scale });

        try {
            return {
                points: runGrabcut(),
                shapeType: ShapeType.Polygon,
            };
        } finally {
            resizedImg.delete();
        }
    }

    runGrabcutRect({ roiRect, resizedImg, scale }: GrabcutDependencies): Point[] {
        const { width, height } = roiRect;
        const initMask = new CV.Mat(width, height, CV.CV_8U, new CV.Scalar(CV.GC_PR_BGD)) as OpenCVTypes.Mat;
        let resizedMask = this.resize(initMask, scale);
        const selectionRoiRect = this.getSelection(resizedImg);

        CV.grabCut(resizedImg, resizedMask, selectionRoiRect, this.bgdModel, this.fgdModel, 2, CV.GC_INIT_WITH_RECT);
        resizedMask = this.maxSideResize(resizedMask, scale, { width, height });

        try {
            return this.extractPolygons(resizedMask, roiRect, scale);
        } finally {
            this.mask.delete();
            this.mask = resizedMask.clone();
            resizedMask?.delete();
        }
    }

    runGrabcutMask({
        scale,
        activeTool,
        resizedImg,
        strokeWidth,
        roiRect,
        foreground = [],
        background = [],
    }: GrabcutData & GrabcutDependencies): Point[] {
        const markersMask = this.mask.clone();
        this.applyMarkersByOrder(markersMask, activeTool, foreground, background, strokeWidth, roiRect);
        let resizedMask = this.resize(markersMask, scale);

        CV.grabCut(resizedImg, resizedMask, new CV.Rect(), this.bgdModel, this.fgdModel, 2, CV.GC_INIT_WITH_MASK);

        resizedMask = this.maxSideResize(resizedMask, scale, {
            width: roiRect.width,
            height: roiRect.height,
        });

        try {
            return this.extractPolygons(resizedMask, roiRect, scale);
        } finally {
            resizedMask?.delete();
        }
    }

    getSelection(img: OpenCVTypes.Mat): OpenCVTypes.Rect {
        return new CV.Rect(1, 1, img.cols - 2, img.rows - 2);
    }

    extractPolygons(src: OpenCVTypes.Mat, roiRect: OpenCVTypes.Rect, scale: number): Point[] {
        let thresholdMask;
        let contours;
        let contour;
        let points = [];

        try {
            thresholdMask = this.threshold(src);
            this.removeBorderContour(thresholdMask, scale);
            contours = this.getContours(thresholdMask);
            contour = this.getPolygonWithLargestArea(contours);
            points = this.closePoints(this.formatContourToPoints(contour, roiRect));

            return points;
        } finally {
            contour?.delete();
            contours?.delete();
            thresholdMask?.delete();
        }
    }

    removeBorderContour(src: OpenCVTypes.Mat, scale: number): void {
        if (scale > 1) {
            new CV.rectangle(src, { x: 0, y: 0 }, { x: src.cols, y: src.rows }, new CV.Scalar(CV.GC_BGD), 8);
        }
    }

    threshold(src: OpenCVTypes.Mat): OpenCVTypes.Mat {
        const fgMask = new CV.Mat();
        const prFgMask = new CV.Mat();
        const finalMask = new CV.Mat();
        const white = 255;

        try {
            CV.threshold(src, prFgMask, CV.GC_PR_BGD, white, CV.THRESH_BINARY);
            CV.threshold(src, fgMask, CV.GC_FGD, 0, CV.THRESH_TOZERO_INV);
            CV.threshold(fgMask, fgMask, CV.GC_BGD, white, CV.THRESH_BINARY);
            CV.bitwise_or(prFgMask, fgMask, finalMask);

            return finalMask;
        } finally {
            fgMask?.delete();
            prFgMask?.delete();
        }
    }

    getImage(imageData: ImageData): OpenCVTypes.Mat {
        const data = CV.matFromImageData(imageData);
        CV.cvtColor(data, data, CV.COLOR_RGBA2RGB, 0);
        return data;
    }

    formatRoiRect(rect: Rect): OpenCVTypes.Rect {
        return new CV.Rect(rect.x, rect.y, rect.width, rect.height);
    }

    applyMarkersByOrder(
        src: OpenCVTypes.Mat,
        activeTool: GrabcutToolType,
        foreground: Point[][],
        background: Point[][],
        strokeWidth: number,
        rectOffset: OpenCVTypes.Rect
    ): void {
        const applyBackgroundOrNothing = () =>
            background.length && this.applyMarkers(src, background, CV.GC_BGD, strokeWidth, rectOffset);

        const applyForegroundOrNothing = () =>
            foreground.length && this.applyMarkers(src, foreground, CV.GC_FGD, strokeWidth, rectOffset);

        if (activeTool === GrabcutToolType.ForegroundTool) {
            applyBackgroundOrNothing();
            applyForegroundOrNothing();
        }
        if (activeTool === GrabcutToolType.BackgroundTool) {
            applyForegroundOrNothing();
            applyBackgroundOrNothing();
        }
    }

    applyMarkers(
        src: OpenCVTypes.Mat,
        markers: Point[][],
        colorIdx: number,
        strokeWidth: number,
        rectOffset: OpenCVTypes.Rect
    ): void {
        const markersVector = new CV.MatVector();

        markers.forEach((marker) => {
            const marketMat = getMatFromPoints(CV, marker, { x: -rectOffset.x, y: -rectOffset.y });
            markersVector.push_back(marketMat);
            marketMat.delete();
        });

        CV.polylines(src, markersVector, false, new CV.Scalar(colorIdx), strokeWidth);
        markersVector.delete();
    }

    cropAndResize(src: OpenCVTypes.Mat, roiRect: OpenCVTypes.Rect, scale: number): OpenCVTypes.Mat {
        const roiSrc = this.cropArea(src, roiRect);
        return this.resize(roiSrc, scale);
    }

    resize(src: OpenCVTypes.Mat, scale: number): OpenCVTypes.Mat {
        const size = new CV.Size(src.cols / scale, src.rows / scale);

        return this.maxSideResize(src, scale, size);
    }

    cropArea(src: OpenCVTypes.Mat, rect: OpenCVTypes.Rect): OpenCVTypes.Mat {
        let dst = new CV.Mat();

        dst = src.roi(rect);

        return dst;
    }

    maxSideResize(src: OpenCVTypes.Mat, scale: number, size: OpenCVTypes.Size): OpenCVTypes.Mat {
        if (scale > 1) {
            const dst = new CV.Mat();

            CV.resize(src, dst, size, 0, 0, CV.INTER_AREA);
            src.delete();

            return dst;
        }

        return src;
    }

    getScale(rect: OpenCVTypes.Rect, sensitivity: number): number {
        return Math.max(rect.width, rect.height) / Math.pow(sensitivity, 2);
    }

    getContours(src: OpenCVTypes.Mat): OpenCVTypes.MatVector {
        const contours = new CV.MatVector();

        CV.findContours(src, contours, new CV.Mat(), CV.RETR_EXTERNAL, CV.CHAIN_APPROX_SIMPLE);

        return contours;
    }

    formatContourToPoints(contour: OpenCVTypes.Mat, rectOffset: OpenCVTypes.Rect): Point[] {
        if (!contour?.rows) {
            return [];
        }

        const newContour = approximateShape(CV, contour);
        const points = getPointsFromMat(newContour, rectOffset);
        newContour?.delete();
        return points;
    }

    closePoints(points: Point[]): Point[] {
        if (!points.length) {
            return points;
        }

        const [first] = points;

        return [...points, { x: first.x, y: first.y }];
    }

    getPolygonWithLargestArea(contours: OpenCVTypes.MatVector): OpenCVTypes.Mat {
        let maxContour = contours.get(0);
        let maxArea = -1;
        let maxSize = -1;

        for (let idx = 0; idx < contours.size(); idx++) {
            const contour = contours.get(idx);

            // https://docs.CV.org/master/d3/dc0/group__imgproc__shape.html#ga2c759ed9f497d4a618048a2f56dc97f1
            const area = CV.contourArea(contour, false);
            const [rows, cols] = contour.matSize;
            const currentMaxSize = rows + cols;

            if (area > maxArea && currentMaxSize > maxSize) {
                maxArea = area;
                maxContour = contour;
                maxSize = currentMaxSize;
            }
        }

        return maxContour;
    }

    cleanModels(): void {
        this.img?.delete();
        this.mask?.delete();
        this.bgdModel?.delete();
        this.fgdModel?.delete();
    }
}

const WorkerApi = { Grabcut, waitForOpenCV, terminate };

expose(WorkerApi);
