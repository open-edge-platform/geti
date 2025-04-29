// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { WebWorker } from '../../../../webworkers/web-worker.interface';

export interface InferenceImageMethods {
    cleanModels: () => void;
    resize: (imageData: ImageData, width: number, height: number) => ImageData;
}

export interface InferenceImageInstance {
    new (): InferenceImageMethods;
}

export interface InferenceImageWorker extends WebWorker<ImageData> {
    InferenceImage: InferenceImageInstance;
    type: AlgorithmType.INFERENCE_IMAGE;
}
