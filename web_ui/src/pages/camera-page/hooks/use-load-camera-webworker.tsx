// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
