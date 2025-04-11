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

interface RITMInstance {
    new (): Promise<RITMMethods>;
}

export interface RITMWorker extends WebWorker<Polygon> {
    RITM: RITMInstance;
    type: AlgorithmType.RITM;
}

export interface RITMData {
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
