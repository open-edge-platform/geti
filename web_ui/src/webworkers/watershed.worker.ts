// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OpenCVLoader, Watershed, WatershedInstance } from '@geti/smart-tools';
import { expose, proxy, ProxyMarked } from 'comlink';
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

const initWatershed = async (imageData: ImageData): Promise<WatershedInstance & ProxyMarked> => {
    if (!opencv) {
        throw new Error('OpenCV is not loaded. Please load OpenCV before running Watershed.');
    }

    return proxy(new Watershed(opencv, imageData));
};

const WorkerApi = {
    Watershed: initWatershed,
    terminate: self.close,
    waitForOpenCV,
};

expose(WorkerApi);
