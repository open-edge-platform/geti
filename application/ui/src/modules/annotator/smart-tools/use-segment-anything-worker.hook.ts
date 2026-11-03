// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n } from '@/i18n';
import { queryOptions, useQuery } from '@tanstack/react-query';
import { Remote, wrap } from 'comlink';

import { executeWithTimeout } from './execute-with-timeout';
import { SAM_WORKER_BUILD_TIMEOUT_MS, SAM_WORKER_INIT_TIMEOUT_MS } from './sam-timeouts';
import type {
    SegmentAnythingWorkerApi,
    SegmentAnythingWorkerInstance,
} from './webworkers/segment-anything.worker.interface';

export type SegmentAnythingRemoteInstance = Remote<SegmentAnythingWorkerInstance>;

// `gcTime: Infinity` is critical: the default 5-min gc would evict the worker
// entry whenever SAM is unmounted (switching tools/projects), causing the
// next mount to spawn a brand-new worker that re-downloads the ORT wasm +
// JSEP `.mjs` glue + the multi-MB SAM `.onnx` models. It would also leak the
// previous worker, since tanstack doesn't fire the abort signal on gc — only
// on cancellation of an in-flight query. Keeping the entry alive for the
// lifetime of the page reuses the same worker (and its resident sessions)
// across every mount.
const segmentAnythingWorkerQueryOptions = (enabled = true) =>
    queryOptions<{ worker: Worker; instance: SegmentAnythingRemoteInstance }>({
        queryKey: ['workers', 'SEGMENT_ANYTHING'],
        queryFn: async ({ signal }) => {
            const worker = new Worker(new URL('./webworkers/segment-anything.worker', import.meta.url), {
                type: 'module',
            });
            // Terminate the worker if the query is cancelled (e.g. annotator unmounts)
            // before build/init resolve, so we don't leak the in-flight worker.
            //
            // CRITICAL: pass an arrow function, NOT `worker.terminate` directly.
            // addEventListener invokes the listener with `this = signal`, and
            // `Worker.prototype.terminate` requires `this` to be a Worker — it
            // throws "Illegal invocation" silently and the worker is never
            // killed. With React StrictMode double-mounting effects (or any
            // transient cancellation), every cycle leaked a fresh worker, each
            // of which independently re-fetched opencv (~1MB), the ort bundle,
            // ort wasm, and the SAM `.onnx` models. That was the dominant
            // source of the "ort/opencv fetched 6 times" symptom.
            signal.addEventListener('abort', () => worker.terminate(), { once: true });

            try {
                const samWorker = wrap<SegmentAnythingWorkerApi>(worker);
                const instance = await executeWithTimeout(
                    samWorker.build(),
                    i18n.t('annotator.tools.autoSegmentation.operations.workerBuild'),
                    SAM_WORKER_BUILD_TIMEOUT_MS
                );

                // Only the decoder runs locally; image embeddings come from the backend.
                await executeWithTimeout(
                    instance.init('SEGMENT_ANYTHING_DECODER'),
                    i18n.t('annotator.tools.autoSegmentation.operations.workerInit'),
                    SAM_WORKER_INIT_TIMEOUT_MS
                );

                if (signal.aborted) {
                    throw signal.reason;
                }

                return { worker, instance };
            } catch (error) {
                worker.terminate();

                throw error;
            }
        },
        staleTime: Infinity,
        gcTime: Infinity,
        enabled,
    });

export const useSegmentAnythingWorker = (enabled = true) => {
    return useQuery({
        ...segmentAnythingWorkerQueryOptions(enabled),
        select: (data) => data.instance,
    });
};
