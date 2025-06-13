// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { Point, Polygon, Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';

export interface RITMPoint {
    x: number;
    y: number;
    positive: boolean;
}

interface RITMMinAreaRect {
    angle: number;
    center: { x: number; y: number };
    size: { width: number; height: number };
}

export interface RITMResult {
    points: RITMPoint[];
    shape: Shape | undefined;
}

export interface RITMWorker extends WebWorker<Polygon> {
    RITM: (imageData: ImageData) => Promise<RITMMethods>;
    type: AlgorithmType.RITM;
}

export interface RITMData {
    imageData: ImageData;
    area: RegionOfInterest;
    givenPoints: RITMPoint[];
    outputShape: ShapeType;
}

export interface RITMContour {
    contour: Point[];
    area: number;
    score: number;
    minAreaRect: RITMMinAreaRect;
}

export const defaultRITMConfig = {
    dynamicBoxMode: true,
    rightClickMode: false,
};

export const TEMPLATE_SIZE = 384;

export interface RITMMethods {
    loadImage(imageData: ImageData): void;
    load(): void;
    reset(): void;
    cleanMemory(): void;
    execute(imageArea: RegionOfInterest, points: RITMPoint[], outputShape: ShapeType): Promise<Shape | undefined>;
    resetPointMask(): void;
}
