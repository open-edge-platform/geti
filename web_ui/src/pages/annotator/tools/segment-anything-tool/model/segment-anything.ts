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

import type OpenCVTypes from 'OpenCVTypes';

import { AlgorithmType } from '../../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { OpenCVPreprocessorConfig } from './pre-processing';
import { SegmentAnythingDecoder, SegmentAnythingPrompt } from './segment-anything-decoder';
import { EncodingOutput, SegmentAnythingEncoder } from './segment-anything-encoder';
import { SegmentAnythingResult } from './segment-anything-result';
import { Session } from './session';

type cv = typeof OpenCVTypes;

const createSession = async (modelPath: string): Promise<Session> => {
    const session = new Session();
    await session.init(modelPath);
    return session;
};

export class SegmentAnythingModel {
    private sessions = new Map<string, Session>();
    private modelPaths: Map<string, string>;
    private preProcessorConfig: OpenCVPreprocessorConfig;

    public constructor(
        private cv: cv,
        modelPaths: Map<string, string>,
        preProcessorConfig: OpenCVPreprocessorConfig
    ) {
        this.modelPaths = modelPaths;
        this.preProcessorConfig = preProcessorConfig;
    }

    public async init(
        algorithm: AlgorithmType.SEGMENT_ANYTHING_DECODER | AlgorithmType.SEGMENT_ANYTHING_ENCODER
    ): Promise<void> {
        if (!this.sessions.has('encoder') && algorithm === AlgorithmType.SEGMENT_ANYTHING_ENCODER) {
            const encoderPath = this.modelPaths.get('encoder') ?? '';
            this.sessions.set('encoder', await createSession(encoderPath));
        }

        if (!this.sessions.has('decoder') && algorithm === AlgorithmType.SEGMENT_ANYTHING_DECODER) {
            const decoderPath = this.modelPaths.get('decoder') ?? '';
            this.sessions.set('decoder', await createSession(decoderPath));
        }
    }

    public async processEncoder(initialImageData: ImageData): Promise<EncodingOutput> {
        const session = this.sessions.get('encoder');

        if (!session) {
            throw Error('the encoder is absent in the sessions map');
        }

        const encoder = new SegmentAnythingEncoder(this.cv, this.preProcessorConfig, session);

        return await encoder.processEncoder(initialImageData);
    }

    public async processDecoder(
        encodingOutput: EncodingOutput,
        input: SegmentAnythingPrompt
    ): Promise<SegmentAnythingResult> {
        const session = this.sessions.get('decoder');
        if (!session) {
            throw Error('the decoder is absent in the sessions map');
        }

        const decoder = new SegmentAnythingDecoder(this.cv, session);
        const output = await decoder.process(encodingOutput, input);

        if (output.shapes.length === 0) {
            return {
                areas: [],
                maxContourIdx: 0,
                shapes: [],
            };
        }

        return {
            areas: [output.areas[output.maxContourIdx]],
            maxContourIdx: output.maxContourIdx,
            shapes: [output.shapes[output.maxContourIdx]],
        };
    }
}
