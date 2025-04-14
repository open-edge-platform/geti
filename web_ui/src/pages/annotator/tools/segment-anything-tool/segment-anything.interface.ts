// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';
import { SegmentAnythingModel } from './model/segment-anything';

export interface InteractiveAnnotationPoint {
    x: number;
    y: number;
    positive: boolean;
}

interface SegmentAnythingWorker extends WebWorker<InteractiveAnnotationPoint> {
    model: SegmentAnythingModel;
}

export interface SegmentAnythingEncoderWorker extends SegmentAnythingWorker {
    type: AlgorithmType.SEGMENT_ANYTHING_ENCODER;
}

export interface SegmentAnythingDecoderWorker extends SegmentAnythingWorker {
    type: AlgorithmType.SEGMENT_ANYTHING_DECODER;
}
