// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent } from 'react';

import { Point, Polygon } from '../../../../core/annotations/shapes.interface';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';
import { Hotkeys } from '../../providers/annotator-provider/utils';
import { PolygonMode } from './polygon-tool.enum';

interface IntelligentScissorsInstance {
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
