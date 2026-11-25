// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SegmentAnythingModels } from '@geti-ui/smart-tools/segment-anything';

import { OPENCV_SOURCE_PATH } from './opencv-source';

export const ORT_WASM_ROOT = `${process.env.ASSET_PREFIX}/ort/`;

// What smart-tools and ONNX Runtime download while building the SAM worker.
const SEGMENT_ANYTHING_ASSETS = [
    OPENCV_SOURCE_PATH,
    `${ORT_WASM_ROOT}ort-wasm-simd-threaded.jsep.wasm`,
    SegmentAnythingModels.decoder,
];

const download = async (url: string, stallTimeoutMs: number): Promise<void> => {
    const controller = new AbortController();
    let stallTimer: ReturnType<typeof setTimeout> | undefined;

    const restartStallTimer = () => {
        clearTimeout(stallTimer);
        stallTimer = setTimeout(() => {
            controller.abort(new Error(`No data received for ${stallTimeoutMs / 1000}s while downloading ${url}`));
        }, stallTimeoutMs);
    };

    try {
        restartStallTimer();

        const response = await fetch(url, { signal: controller.signal });

        if (!response.ok || response.body === null) {
            throw new Error(`Failed to download ${url} (${response.status})`);
        }

        const reader = response.body.getReader();

        while (!(await reader.read()).done) {
            restartStallTimer();
        }
    } catch (error) {
        throw controller.signal.aborted ? controller.signal.reason : error;
    } finally {
        clearTimeout(stallTimer);
    }
};

// Downloads the assets into the browser cache, where smart-tools and ONNX Runtime then find them, so the
// build/init timeouts measure compilation rather than a slow first download. A download only fails once
// no data has arrived for `stallTimeoutMs`.
export const prefetchSegmentAnythingAssets = async (stallTimeoutMs: number): Promise<void> => {
    await Promise.all(SEGMENT_ANYTHING_ASSETS.map((url) => download(url, stallTimeoutMs)));
};
