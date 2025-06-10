// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Label, Point } from '../shared/interfaces';

export interface WatershedPolygon {
    id: number;
    label: Label;
    points: Point[];
}

export type Marker = {
    label: Label;
    points: Point[];
    brushSize: number;
    id: number;
};

export interface WatershedMethods {
    executeWatershed(markers: Marker[], sensitivity: number): WatershedPolygon[];
    clearMemory: () => void;
}
