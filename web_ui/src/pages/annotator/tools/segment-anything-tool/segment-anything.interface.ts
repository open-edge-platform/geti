// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
