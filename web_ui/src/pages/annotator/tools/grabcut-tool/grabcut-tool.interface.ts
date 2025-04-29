// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Point, Polygon, Rect } from '../../../../core/annotations/shapes.interface';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';
import { Hotkeys } from '../../providers/annotator-provider/utils';
import { GrabcutToolType } from './grabcut-tool.enums';

export interface GrabcutData {
    inputRect: Rect;
    strokeWidth: number;
    sensitivity: number;
    foreground: Point[][];
    background: Point[][];
    image: ImageData;
    activeTool: GrabcutToolType;
}

export interface GrabcutWorker extends WebWorker<Polygon> {
    Grabcut: GrabcutInstance;
    type: AlgorithmType.GRABCUT;
}

interface GrabcutInstance {
    new (imageData: ImageData): GrabcutMethods;
}

export interface GrabcutMethods {
    startGrabcut: (data: Omit<GrabcutData, 'image'>) => Polygon;
    cleanModels: () => void;
}

export const GrabcutHotKeys: Pick<Hotkeys, GrabcutToolType> = {
    [GrabcutToolType.InputTool]: 'g',
    [GrabcutToolType.ForegroundTool]: 'shift',
    [GrabcutToolType.BackgroundTool]: 'alt',
};
