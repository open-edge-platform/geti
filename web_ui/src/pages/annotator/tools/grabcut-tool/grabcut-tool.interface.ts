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
