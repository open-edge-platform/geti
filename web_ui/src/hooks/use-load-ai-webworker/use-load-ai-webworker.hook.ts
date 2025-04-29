// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useQuery } from '@tanstack/react-query';
import { wrap } from 'comlink';

import { AlgorithmType } from './algorithm.interface';
import { MapAlgorithmToWorker } from './load-webworker.interface';
import { getWorker } from './utils';

export const useLoadAIWebworker = <T extends AlgorithmType>(algorithmType: T) => {
    const { data, isLoading, isSuccess, isError } = useQuery({
        queryKey: ['workers', algorithmType],
        queryFn: async () => {
            const baseWorker = getWorker(algorithmType);
            const worker = wrap<MapAlgorithmToWorker[T]>(baseWorker);

            await worker.waitForOpenCV();

            return worker;
        },
        staleTime: Infinity,
    });

    return { worker: data, isLoading, isSuccess, isError };
};
