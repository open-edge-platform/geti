// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useQuery } from '@tanstack/react-query';
import { Remote, wrap } from 'comlink';

import { Screenshot } from '../../camera-support/camera.interface';
import { useCameraStoreName } from './use-camera-store-name.hook';

export interface CameraWorkerMethods extends LocalForageDbMethodsCore {
    getItems: () => Promise<Screenshot[]>;
    updateMedia: (key: string, screenshot: Omit<Screenshot, 'id'>) => Promise<void>;
    terminate: () => void;
}

interface CameraWorkerInstance {
    new (storeName: string): Promise<CameraWorkerMethods>;
}

interface CameraWorker {
    Camera: CameraWorkerInstance;
}

interface UseLoadCameraWebworker {
    worker: CameraWorkerMethods | undefined;
    isLoading: boolean;
    isSuccess: boolean;
    isError: boolean;
    terminateWorker: () => void;
}

export const useLoadCameraWebworker = (): UseLoadCameraWebworker => {
    const storeName = useCameraStoreName();

    const { data, isLoading, isSuccess, isError } = useQuery({
        queryKey: ['workers', storeName],
        queryFn: async () => {
            const worker: Remote<CameraWorker> = wrap(
                new Worker(new URL('../../../webworkers/camera.worker', import.meta.url))
            );

            const instance = await new worker.Camera(storeName);

            return instance;
        },
        staleTime: Infinity,
    });

    const terminateWorker = () => {
        if (data) {
            data.terminate();
        }
    };

    return { worker: data, isLoading, isSuccess, isError, terminateWorker };
};
