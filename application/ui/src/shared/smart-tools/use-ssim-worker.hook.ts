// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n } from '@/i18n';
import { useQuery } from '@tanstack/react-query';
import { Remote, wrap } from 'comlink';

import { executeWithTimeout } from './execute-with-timeout';
import type { SSIMWorkerApi, SSIMWorkerInstance } from './webworkers/ssim-worker.interface';

// Building the worker downloads and compiles the OpenCV wasm, which can be slow on a cold cache.
const SSIM_WORKER_BUILD_TIMEOUT_MS = 30_000;
export const SSIM_WORKER_QUERY_KEY = ['workers', 'SSIM'];

export const useSSIMWorker = (enabled = true) => {
    const { data, isLoading, isError, error } = useQuery<{ worker: Worker; instance: Remote<SSIMWorkerInstance> }>({
        queryKey: SSIM_WORKER_QUERY_KEY,
        queryFn: async ({ signal }) => {
            const worker = new Worker(new URL('./webworkers/ssim-worker', import.meta.url), {
                type: 'module',
            });
            // Wrap in an arrow so `terminate` is called as a method on `worker` (this === worker);
            // passing `worker.terminate` directly would invoke it with `this === signal` → "Illegal invocation".
            signal.addEventListener('abort', () => worker.terminate(), { once: true });

            try {
                const instance = await executeWithTimeout(
                    wrap<SSIMWorkerApi>(worker).build(),
                    i18n.t('annotator.tools.ssim.operations.workerBuild'),
                    SSIM_WORKER_BUILD_TIMEOUT_MS
                );

                if (signal.aborted) {
                    throw signal.reason;
                }

                return { worker, instance };
            } catch (buildError) {
                worker.terminate();

                throw buildError;
            }
        },
        staleTime: Infinity,
        // Tanstack doesn't abort on gc, so evicting the entry would leak the worker; it is
        // terminated by `useTerminateSmartToolWorkersOnUnmount` instead.
        gcTime: Infinity,
        enabled,
    });

    return { worker: data?.instance, rawWorker: data?.worker, isLoading, isError, error };
};
