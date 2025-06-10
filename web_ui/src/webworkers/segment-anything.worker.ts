// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//  Dependencies get bundled into the worker

import { OpenCVLoader } from '@geti/smart-tools';
import { expose } from 'comlink';
import type OpenCVTypes from 'OpenCVTypes';

import { AlgorithmType } from '../hooks/use-load-ai-webworker/algorithm.interface';
import { SegmentAnythingModel } from '../pages/annotator/tools/segment-anything-tool/model/segment-anything';
import { SegmentAnythingPrompt } from '../pages/annotator/tools/segment-anything-tool/model/segment-anything-decoder';
import { EncodingOutput } from '../pages/annotator/tools/segment-anything-tool/model/segment-anything-encoder';
import { SegmentAnythingResult } from '../pages/annotator/tools/segment-anything-tool/model/segment-anything-result';

declare const self: DedicatedWorkerGlobalScope;

let CV: OpenCVTypes.cv | null = null;

const terminate = (): void => {
    self.close();
};

const waitForOpenCV = async (): Promise<boolean> => {
    if (CV) {
        return true;
    } else {
        return OpenCVLoader().then((cvInstance: OpenCVTypes.cv) => {
            CV = cvInstance;

            return true;
        });
    }
};

class SegmentAnythingModelWrapper {
    private model: SegmentAnythingModel;
    constructor() {
        const config = {
            preProcessorConfig: {
                normalize: {
                    enabled: true,
                    mean: [0.485, 0.456, 0.406],
                    std: [0.229, 0.224, 0.225],
                },
                resize: true,
                size: 1024,
                squareImage: false,
                pad: true,
                padSize: 1024,
            },
            modelPaths: new Map([
                ['encoder', new URL('./segment-anything/mobile_sam.encoder.onnx', import.meta.url).toString()],
                ['decoder', new URL('./segment-anything/sam_vit_h_4b8939.decoder.onnx', import.meta.url).toString()],
            ]),
        };

        this.model = new SegmentAnythingModel(CV, config.modelPaths, config.preProcessorConfig);
    }

    public async init(
        algorithm: AlgorithmType.SEGMENT_ANYTHING_DECODER | AlgorithmType.SEGMENT_ANYTHING_ENCODER
    ): Promise<void> {
        await this.model.init(algorithm);
    }
    public async processEncoder(initialImageData: ImageData): Promise<EncodingOutput> {
        return this.model.processEncoder(initialImageData);
    }

    public async processDecoder(
        encodingOutput: EncodingOutput,
        input: SegmentAnythingPrompt
    ): Promise<SegmentAnythingResult> {
        return this.model.processDecoder(encodingOutput, input);
    }
}

const WorkerApi = {
    model: SegmentAnythingModelWrapper,
    terminate,
    waitForOpenCV,
};

expose(WorkerApi);
