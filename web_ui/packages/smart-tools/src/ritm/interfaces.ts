// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as ort from 'onnxruntime-web';

import { Point } from '../shared/interfaces';

export interface MainModelResponse {
    instances: ort.Tensor;
    instances_aux: ort.Tensor;
    feature: ort.Tensor;
}

export interface Models {
    preprocess: ort.InferenceSession;
    main: ort.InferenceSession;
}

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

export interface RITMContour {
    contour: Point[];
    area: number;
    score: number;
    minAreaRect: RITMMinAreaRect;
}

export const TEMPLATE_SIZE = 384;
