// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import type * as Comlink from 'comlink';
import * as ort from 'onnxruntime-common';
import type OpenCVTypes from 'OpenCVTypes';

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
