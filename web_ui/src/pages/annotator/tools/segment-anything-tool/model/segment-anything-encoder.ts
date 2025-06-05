// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as OpenCVTypes from '@geti/smart-tools/opencv-types';
import type * as Comlink from 'comlink';
import * as ort from 'onnxruntime-common';

import { OpenCVPreprocessor, OpenCVPreprocessorConfig } from './pre-processing';
import { type Session } from './session';

type cv = typeof OpenCVTypes;

type ModelSession = Session | Comlink.Remote<Session>;

export type EncodingOutput = {
    encoderResult: ort.Tensor;
    originalWidth: number;
    originalHeight: number;
    newWidth: number;
    newHeight: number;
};

export class SegmentAnythingEncoder {
    private preprocessor: OpenCVPreprocessor;

    constructor(
        cv: cv,
        config: OpenCVPreprocessorConfig,
        private session: ModelSession
    ) {
        this.preprocessor = new OpenCVPreprocessor(cv, config);
    }

    public async processEncoder(initialImageData: ImageData) {
        const result = this.preprocessor.process(initialImageData);
        console.time('[SAM] Encoding');
        const outputData = await this.session.run({ x: result.tensor });
        console.timeEnd('[SAM] Encoding');

        const outputNames = await this.session.outputNames();
        const encoderResult = outputData[outputNames[0]];

        const originalWidth = initialImageData.width;
        const originalHeight = initialImageData.height;
        const newWidth = result.newWidth;
        const newHeight = result.newHeight;

        return {
            encoderResult,
            originalWidth,
            originalHeight,
            newWidth,
            newHeight,
        };
    }
}
