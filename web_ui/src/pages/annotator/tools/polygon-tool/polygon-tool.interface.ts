// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { PointerEvent } from 'react';

import { Point, Polygon } from '../../../../core/annotations/shapes.interface';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';
import { Hotkeys } from '../../providers/annotator-provider/utils';
import { PolygonMode } from './polygon-tool.enum';

export interface IntelligentScissorsInstance {
    new (imageData: ImageData): IntelligentScissorsMethods;
}

export interface IntelligentScissorsWorker extends WebWorker<Polygon> {
    IntelligentScissors: IntelligentScissorsInstance;
    type: AlgorithmType.INTELLIGENT_SCISSORS;
    optimizeSegments: (segments: Point[][]) => Promise<Polygon>;
    optimizePolygon: (prevPolygon: Polygon) => Promise<Polygon>;
}

export interface IntelligentScissorsMethods {
    hasInitialPoint: boolean;
    loadTool: () => void;
    cleanImg: () => void;
    cleanPoints: () => void;
    buildMap: (points: { x: number; y: number }) => void;
    calcPoints: (points: { x: number; y: number }) => Point[];
}

export const PolygonHotKeys: Pick<Hotkeys, PolygonMode.MagneticLasso> = {
    [PolygonMode.MagneticLasso]: 'shift+s',
};

export interface MouseEventHandlers {
    onPointerUp: (event: PointerEvent<SVGSVGElement>) => void;
    onPointerDown: (event: PointerEvent<SVGSVGElement>) => void;
    onPointerMove: (event: PointerEvent<SVGSVGElement>) => void;
}
