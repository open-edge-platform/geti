// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OpenCVLoader, RITM } from '@geti/smart-tools';
import { expose, proxy } from 'comlink';
import type OpenCVTypes from 'OpenCVTypes';

declare const self: DedicatedWorkerGlobalScope;

let opencv: OpenCVTypes;

const waitForOpenCV = async () => {
    if (opencv) return true;

    opencv = await OpenCVLoader();

    if ('ready' in opencv) {
        await opencv.ready;
    }

    return false;
};

const initRITM = async (imageData: ImageData) => {
    if (!opencv) {
        throw new Error('OpenCV is not loaded. Please load OpenCV before running RITM.');
    }

    return proxy(await RITM.loadRITM(opencv, imageData));
};

const WorkerApi = {
    RITM: initRITM,
    terminate: self.close,
    waitForOpenCV,
};

expose(WorkerApi);
