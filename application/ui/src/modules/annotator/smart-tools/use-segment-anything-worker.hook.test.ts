// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { QueryClient } from '@tanstack/react-query';
import { renderHook } from 'test-utils/render';

import {
    useRestartSegmentAnythingWorker,
    type SegmentAnythingRemoteInstance,
} from './use-segment-anything-worker.hook';

const SEGMENT_ANYTHING_WORKER_QUERY_KEY = ['workers', 'SEGMENT_ANYTHING'];

const mockInstance = () => ({}) as unknown as SegmentAnythingRemoteInstance;

const setupCachedWorker = () => {
    const queryClient = new QueryClient();
    const worker = { terminate: rs.fn() } as unknown as Worker;
    const instance = mockInstance();

    queryClient.setQueryData(SEGMENT_ANYTHING_WORKER_QUERY_KEY, { worker, instance });

    const { result } = renderHook(() => useRestartSegmentAnythingWorker(), { queryClient });

    return { queryClient, worker, instance, restartWorker: result.current };
};

describe('useRestartSegmentAnythingWorker', () => {
    it('terminates the stuck worker and drops it from the cache', () => {
        const { queryClient, worker, instance, restartWorker } = setupCachedWorker();

        restartWorker(instance);

        expect(worker.terminate).toHaveBeenCalledTimes(1);
        expect(queryClient.getQueryData(SEGMENT_ANYTHING_WORKER_QUERY_KEY)).toBeUndefined();
    });

    it('leaves the current worker alone when the stuck instance was already replaced', () => {
        const { queryClient, worker, instance, restartWorker } = setupCachedWorker();

        restartWorker(mockInstance());

        expect(worker.terminate).not.toHaveBeenCalled();
        expect(queryClient.getQueryData<{ instance: unknown }>(SEGMENT_ANYTHING_WORKER_QUERY_KEY)?.instance).toBe(
            instance
        );
    });
});
