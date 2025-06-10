// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//  Dependencies get bundled into the worker

import { OpenCVLoader } from '@geti/smart-tools';
import { expose } from 'comlink';
import type OpenCVTypes from 'OpenCVTypes';

import { formatImageData } from './utils';

declare const self: DedicatedWorkerGlobalScope;

let CV: OpenCVTypes.cv | null = null;

const terminate = (): void => {
    self.close();
};

class InferenceImage {
    resize(imageData: ImageData, width: number, height: number): ImageData {
        const img = this.getImage(imageData);

        const size = new CV.Size(width, height);
        const dst: OpenCVTypes.Mat = new CV.Mat();
        const colorMap: OpenCVTypes.Mat = new CV.Mat();

        CV.resize(img, dst, size, 0, 0, CV.INTER_CUBIC);
        CV.applyColorMap(dst, colorMap, CV.COLORMAP_JET);
        CV.cvtColor(colorMap, colorMap, CV.COLOR_BGR2RGB);

        const finalImageData = formatImageData(CV, colorMap);

        img.delete();
        dst.delete();
        colorMap.delete();

        return finalImageData;
    }

    getImage(imageData: ImageData): OpenCVTypes.Mat {
        const data = CV.matFromImageData(imageData);

        CV.cvtColor(data, data, CV.COLOR_RGBA2RGB, 0);

        return data;
    }
}

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

const WorkerApi = { InferenceImage, waitForOpenCV, terminate };

expose(WorkerApi);
