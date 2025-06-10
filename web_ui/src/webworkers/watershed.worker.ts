// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OpenCVLoader, Watershed } from '@geti/smart-tools';
import { WatershedMethods } from '@geti/smart-tools/src/watershed/interfaces';
import { expose } from 'comlink';
import type OpenCVTypes from 'OpenCVTypes';

declare const self: DedicatedWorkerGlobalScope;

let opencv: OpenCVTypes;

const waitForOpenCV = async () => {
    if (opencv) return opencv;

    opencv = await OpenCVLoader();

    if ('ready' in opencv) {
        await opencv.ready;
    }

    return opencv;
};

const WorkerApi = {
    Watershed: async (imageData: ImageData): Promise<WatershedMethods> => {
        const cv = waitForOpenCV();

        if (!cv) {
            throw new Error('OpenCV not loaded.');
        }

        return new Watershed(cv, imageData);
    },
    terminate: self.close,
    waitForOpenCV,
};

expose(WorkerApi);
