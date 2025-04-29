// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import type { InferenceSession } from 'onnxruntime-common';
import * as ort from 'onnxruntime-web';

import { loadSource } from '../../../../../webworkers/utils';
import { SessionParameters, sessionParams } from '../../wasm-utils';

const loadModel = async (modelPath: string) => {
    return await (await loadSource(modelPath))?.arrayBuffer();
};

export class Session {
    ortSession: InferenceSession | undefined;
    params: SessionParameters;

    constructor() {
        this.params = sessionParams;
    }

    public async init(modelPath: string) {
        ort.env.wasm.numThreads = this.params.numThreads;
        ort.env.wasm.wasmPaths = this.params.wasmRoot;
        ort.env.wasm.simd = true;

        const modelData = await loadModel(modelPath);

        if (!modelData) {
            throw new Error(`Unable to load model from "${modelPath}"`);
        }

        const session = await ort.InferenceSession.create(modelData, {
            executionProviders: this.params.executionProviders,
            graphOptimizationLevel: 'all',
            executionMode: 'parallel',
        });

        this.ortSession = session;
    }

    public async run(input: InferenceSession.OnnxValueMapType): Promise<InferenceSession.OnnxValueMapType> {
        if (!this.ortSession) {
            throw Error('the session is not initialized. Call `init()` method first.');
        }
        return await this.ortSession.run(input);
    }

    public inputNames(): readonly string[] {
        if (!this.ortSession) {
            throw Error('the session is not initialized. Call `init()` method first.');
        }
        return this.ortSession.inputNames;
    }

    public outputNames(): readonly string[] {
        if (!this.ortSession) {
            throw Error('the session is not initialized. Call `init()` method first.');
        }
        return this.ortSession.outputNames;
    }
}
