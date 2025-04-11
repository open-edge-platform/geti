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

import { Point, Polygon } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';
import { Marker } from '../marker-tool/marker-tool.interface';

export interface WatershedPolygon {
    id: number;
    label: Label;
    points: Point[];
}

export interface WatershedWorker extends WebWorker<Polygon> {
    Watershed: WatershedInstance;
    type: AlgorithmType.WATERSHED;
}

interface WatershedInstance {
    new (imageData: ImageData): Promise<WatershedMethods>;
}

export interface WatershedMethods {
    executeWatershed(markers: Marker[], sensitivity: number): WatershedPolygon[];
    clearMemory: () => void;
}

export interface RunWatershedProps {
    imageData: ImageData;
    markers: Marker[];
    sensitivity: number;
}

export interface WatershedLabel {
    markerId: number;
    label: Label;
}
