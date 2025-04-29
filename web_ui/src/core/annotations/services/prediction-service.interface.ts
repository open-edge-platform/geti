// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
