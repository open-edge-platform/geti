// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { waitFor } from '@testing-library/react';
import { wrap } from 'comlink';

import { createQueryClient } from '../../../../query-client/query-client';
import { renderHook } from '../../../../test-utils/render';
import type { SegmentAnythingWorkerBuildOptions } from '../../webworkers/segment-anything.worker.interface';

vi.mock('comlink', () => ({ wrap: vi.fn() }));

const terminate = vi.fn();

class FakeWorker {
    terminate = terminate;
}

const mockWorkerBuild = (build: (options?: SegmentAnythingWorkerBuildOptions) => Promise<unknown>) => {
    const buildSpy = vi.fn(build);
    vi.mocked(wrap).mockReturnValue({ build: buildSpy } as unknown as ReturnType<typeof wrap>);

    return buildSpy;
};

const instance = { init: () => Promise.resolve() };

// The CPU fallback is page-scoped module state, so each test gets a fresh copy of the hook.
const renderWorkerHook = async () => {
    const { useSegmentAnythingWorker } = await import('./use-segment-anything.hook');

    return renderHook(() => useSegmentAnythingWorker(), { queryClient: createQueryClient() });
};

describe('useSegmentAnythingWorker', () => {
    beforeEach(() => {
        vi.resetModules();
        vi.stubGlobal('Worker', FakeWorker);
        terminate.mockClear();
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it('builds the worker with WebGPU allowed when it succeeds', async () => {
        const build = mockWorkerBuild(() => Promise.resolve(instance));

        const { result } = await renderWorkerHook();

        await waitFor(() => expect(result.current.data).toBe(instance));
        expect(build).toHaveBeenCalledTimes(1);
        expect(build).toHaveBeenCalledWith({ cpuOnly: false });
        expect(terminate).not.toHaveBeenCalled();
    });

    it('rebuilds the worker CPU-only when the WebGPU build fails', async () => {
        const build = mockWorkerBuild(({ cpuOnly } = {}) =>
            cpuOnly ? Promise.resolve(instance) : Promise.reject(new Error('webgpu device lost'))
        );

        const { result } = await renderWorkerHook();

        await waitFor(() => expect(result.current.data).toBe(instance));
        expect(build.mock.calls).toEqual([[{ cpuOnly: false }], [{ cpuOnly: true }]]);
        expect(terminate).toHaveBeenCalledTimes(1);
    });

    it('keeps later workers CPU-only after a fallback', async () => {
        const build = mockWorkerBuild(({ cpuOnly } = {}) =>
            cpuOnly ? Promise.resolve(instance) : Promise.reject(new Error('webgpu device lost'))
        );
        const { useSegmentAnythingWorker } = await import('./use-segment-anything.hook');

        const first = renderHook(() => useSegmentAnythingWorker(), { queryClient: createQueryClient() });
        await waitFor(() => expect(first.result.current.data).toBe(instance));

        build.mockClear();
        const second = renderHook(() => useSegmentAnythingWorker(), { queryClient: createQueryClient() });
        await waitFor(() => expect(second.result.current.data).toBe(instance));

        expect(build.mock.calls).toEqual([[{ cpuOnly: true }]]);
    });

    it('surfaces the error when the CPU-only retry also fails', async () => {
        mockWorkerBuild(() => Promise.reject(new Error('model not found')));

        const { result } = await renderWorkerHook();

        await waitFor(() => expect(result.current.isError).toBe(true));
        expect(result.current.error?.message).toBe('model not found');
        expect(terminate).toHaveBeenCalledTimes(2);
    });
});
