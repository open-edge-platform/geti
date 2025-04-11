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

//  Dependencies get bundled into the worker

import { expose } from 'comlink';
import OpenCV from 'opencv';
import type OpenCVTypes from 'OpenCVTypes';

import { formatImageData } from './utils';

let CV: OpenCVTypes.cv | null = null;

OpenCV.then((cvInstance: OpenCVTypes.cv) => {
    CV = cvInstance;
});

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
        return OpenCV.then((cvInstance) => {
            CV = cvInstance;

            return true;
        });
    }
};

const WorkerApi = { InferenceImage, waitForOpenCV, terminate };

expose(WorkerApi);
