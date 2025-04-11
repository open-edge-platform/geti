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
import { Rect, Shape } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';

export const MINIMUM_THRESHOLD = 0.7;

export interface RunSSIMProps {
    imageData: ImageData;
    roi: RegionOfInterest;
    template: Rect;
    existingAnnotations: Shape[];
    autoMergeDuplicates: boolean;
    shapeType: ShapeType;
}

export interface SSIMState {
    shapes: Shape[];
    matches: SSIMMatch[];
    threshold: number;
}

export interface SSIMMatch {
    shape: Rect;
    confidence: number;
}

interface SSIMInstance {
    new (): Promise<SSIMMethods>;
}

export interface SSIMWorker extends WebWorker<Rect> {
    SSIM: SSIMInstance;
    type: AlgorithmType.SSIM;
}

export interface SSIMMethods {
    executeSSIM(runSSIMProps: RunSSIMProps): SSIMMatch[];
}
