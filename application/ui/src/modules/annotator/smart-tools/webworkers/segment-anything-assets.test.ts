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

// Sends one chunk every `intervalMs`, then closes, or never closes when `chunks` is Infinity.
const streamedResponse = (signal: AbortSignal | null | undefined, chunks: number, intervalMs: number) =>
    new Response(
        new ReadableStream<Uint8Array>({
            start(controller) {
                signal?.addEventListener('abort', () => controller.error(signal.reason));

                let sent = 0;
                const send = () => {
                    controller.enqueue(new Uint8Array(1));
                    sent += 1;

                    if (sent >= chunks) {
                        controller.close();
                    } else if (Number.isFinite(chunks)) {
                        setTimeout(send, intervalMs);
                    }
                };

                send();
            },
        })
    );

const mockNetwork = (respond: (url: string, init?: RequestInit) => Response) => {
    const networkFetch = rs.fn(async (input: RequestInfo | URL, init?: RequestInit) => respond(String(input), init));

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
        const networkFetch = mockNetwork((_url, init) => streamedResponse(init?.signal, 1, 0));
        const { prefetchSegmentAnythingAssets } = await loadModule();

        await prefetchSegmentAnythingAssets(STALL_TIMEOUT_MS);

        expect(networkFetch.mock.calls.map(([url]) => url)).toEqual([OPENCV_URL, ORT_WASM_URL, DECODER_URL]);
    });

    it('keeps a slow download going as long as data keeps arriving', async () => {
        rs.useFakeTimers();
        mockNetwork((url, init) => streamedResponse(init?.signal, url === ORT_WASM_URL ? 4 : 1, STALL_TIMEOUT_MS - 1));

        const { prefetchSegmentAnythingAssets } = await loadModule();
        const prefetch = prefetchSegmentAnythingAssets(STALL_TIMEOUT_MS);

        await rs.advanceTimersByTimeAsync(3 * (STALL_TIMEOUT_MS - 1));

        await expect(prefetch).resolves.toBeUndefined();
    });

    it('fails a download once no data arrives for the stall timeout', async () => {
        rs.useFakeTimers();
        mockNetwork((url, init) => streamedResponse(init?.signal, url === ORT_WASM_URL ? Infinity : 1, 0));

        const { prefetchSegmentAnythingAssets } = await loadModule();
        const rejection = expect(prefetchSegmentAnythingAssets(STALL_TIMEOUT_MS)).rejects.toThrow(
            `No data received for 30s while downloading ${ORT_WASM_URL}`
        );

        await rs.advanceTimersByTimeAsync(STALL_TIMEOUT_MS);
        await rejection;
    });

    it('fails when the server does not return the asset', async () => {
        mockNetwork((url, init) =>
            url === DECODER_URL ? new Response(null, { status: 404 }) : streamedResponse(init?.signal, 1, 0)
        );

        const { prefetchSegmentAnythingAssets } = await loadModule();

        await expect(prefetchSegmentAnythingAssets(STALL_TIMEOUT_MS)).rejects.toThrow(
            `Failed to download ${DECODER_URL} (404)`
        );
    });
});
