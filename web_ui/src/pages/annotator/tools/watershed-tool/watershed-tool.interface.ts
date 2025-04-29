// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
