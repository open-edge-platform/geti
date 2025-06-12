// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Point } from '../shared/interfaces';

export interface WatershedPolygon {
    id: number;
    labelId: string;
    points: Point[];
}

export type Marker = {
    labelId: string;
    points: Point[];
    brushSize: number;
    id: number;
};

export interface WatershedMethods {
    executeWatershed: (markers: Marker[], sensitivity: number) => WatershedPolygon[];
    drawMarkers: (markers: Marker[]) => void;
    getPolygons: (markers: Marker[]) => WatershedPolygon[];
    scaleImage: (sensitivity: number) => void;
    clearMemory: () => void;
}
