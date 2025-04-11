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

import { Annotation } from '../annotation.interface';
import { Explanation } from '../prediction.interface';

export interface PredictionResult {
    annotations: ReadonlyArray<Annotation>;
    maps: Explanation[];
}

export interface InferenceServerStatusResult {
    isInferenceServerReady: boolean;
}

export enum PredictionMode {
    AUTO = 'auto',
    ONLINE = 'online',
    LATEST = 'latest',
    VISUAL_PROMPT = 'visual_prompt',
}

export enum PredictionCache {
    AUTO = 'auto',
    NEVER = 'never',
    ALWAYS = 'always',
}

export type PredictionId = PredictionMode | string;
