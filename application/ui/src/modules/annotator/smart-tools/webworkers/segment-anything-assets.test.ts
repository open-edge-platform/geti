// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

rs.mock('@geti-ui/smart-tools/utils', () => ({ setOpenCVSourceUrl: rs.fn() }));
rs.mock('@geti-ui/smart-tools/segment-anything', () => ({
    SegmentAnythingModels: { decoder: '/static/assets/decoder.onnx' },
}));

const OPENCV_URL = '/opencv/opencv.js';
const ORT_WASM_URL = '/ort/ort-wasm-simd-threaded.jsep.wasm';
const DECODER_URL = '/static/assets/decoder.onnx';
const STALL_TIMEOUT_MS = 30_000;

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Sends `chunks` one-byte chunks, each `intervalMs` after the previous one. Like a real fetch,
// the body errors once the request is aborted.
const slowResponse = (signal: AbortSignal, chunks: number, intervalMs: number) => {
    let sent = 0;

    return new Response(
        new ReadableStream<Uint8Array>({
            start: (controller) => signal.addEventListener('abort', () => controller.error(signal.reason)),
            pull: async (controller) => {
                await delay(intervalMs);

                if (sent++ < chunks) {
                    controller.enqueue(new Uint8Array(1));
                } else {
                    controller.close();
                }
            },
        })
    );
};

const mockNetwork = (respond: (url: string, signal: AbortSignal) => Response) => {
    const networkFetch = rs.fn(async (url: string, { signal }: { signal: AbortSignal }) => respond(url, signal));

    rs.stubGlobal('fetch', networkFetch);

    return networkFetch;
};

const loadModule = async () => {
    rs.resetModules();

    return import('./segment-anything-assets');
};

describe('prefetchSegmentAnythingAssets', () => {
    beforeEach(() => {
        rs.stubEnv('ASSET_PREFIX', '');
    });

    afterEach(() => {
        rs.useRealTimers();
        rs.unstubAllGlobals();
        rs.unstubAllEnvs();
    });

    it('downloads every asset the SAM worker loads', async () => {
        const networkFetch = mockNetwork(() => new Response('ok'));
        const { prefetchSegmentAnythingAssets } = await loadModule();

        await prefetchSegmentAnythingAssets(STALL_TIMEOUT_MS);

        expect(networkFetch.mock.calls.map(([url]) => url)).toEqual([OPENCV_URL, ORT_WASM_URL, DECODER_URL]);
    });

    it('keeps a slow download going as long as data keeps arriving', async () => {
        rs.useFakeTimers();
        mockNetwork((url, signal) =>
            url === ORT_WASM_URL ? slowResponse(signal, 3, STALL_TIMEOUT_MS - 1) : new Response('ok')
        );

        const { prefetchSegmentAnythingAssets } = await loadModule();
        const prefetch = prefetchSegmentAnythingAssets(STALL_TIMEOUT_MS);

        await rs.advanceTimersByTimeAsync(4 * (STALL_TIMEOUT_MS - 1));

        await expect(prefetch).resolves.toBeUndefined();
    });

    it('fails a download once no data arrives for the stall timeout', async () => {
        rs.useFakeTimers();
        mockNetwork((url, signal) =>
            url === ORT_WASM_URL ? slowResponse(signal, 1, STALL_TIMEOUT_MS + 1) : new Response('ok')
        );

        const { prefetchSegmentAnythingAssets } = await loadModule();
        const rejection = expect(prefetchSegmentAnythingAssets(STALL_TIMEOUT_MS)).rejects.toThrow(
            `No data received for 30s while downloading ${ORT_WASM_URL}`
        );

        await rs.advanceTimersByTimeAsync(STALL_TIMEOUT_MS);
        await rejection;
    });

    it('fails when the server does not return the asset', async () => {
        mockNetwork((url) => (url === DECODER_URL ? new Response(null, { status: 404 }) : new Response('ok')));

        const { prefetchSegmentAnythingAssets } = await loadModule();

        await expect(prefetchSegmentAnythingAssets(STALL_TIMEOUT_MS)).rejects.toThrow(
            `Failed to download ${DECODER_URL} (404)`
        );
    });
});
