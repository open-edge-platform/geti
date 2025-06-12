// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Point, Polygon } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';
import { Marker } from '../marker-tool/marker-tool.interface';

export interface WatershedWorker extends WebWorker<Polygon> {
    Watershed: (imageData: ImageData) => Promise<WatershedMethods>;
    type: AlgorithmType.WATERSHED;
}

export interface WatershedPolygon {
    id: number;
    label: Label;
    points: Point[];
}

export interface WatershedMethods {
    executeWatershed: (markers: Marker[], sensitivity: number) => WatershedPolygon[];
    drawMarkers: (markers: Marker[]) => void;
    getPolygons: (markers: Marker[]) => WatershedPolygon[];
    scaleImage: (sensitivity: number) => void;
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
