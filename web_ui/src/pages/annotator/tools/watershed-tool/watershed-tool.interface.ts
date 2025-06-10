// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WatershedMethods } from '@geti/smart-tools/src/watershed/interfaces';

import { Polygon } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';
import { Marker } from '../marker-tool/marker-tool.interface';

export interface WatershedWorker extends WebWorker<Polygon> {
    Watershed: (imageData: ImageData) => WatershedMethods;
    type: AlgorithmType.WATERSHED;
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
