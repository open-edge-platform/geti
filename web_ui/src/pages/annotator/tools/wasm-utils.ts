// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface SessionParameters {
    numThreads: number;
    executionProviders: string[];
    wasmRoot?: string | Record<string, string>;
}

const wasmPaths = {
    'ort-wasm.wasm': '/assets/onnx/ort-wasm.wasm',
    'ort-wasm-simd.wasm': '/assets/onnx/ort-wasm-simd.wasm',
    'ort-wasm-threaded.wasm': '/assets/onnx/ort-wasm-threaded.wasm',
    'ort-wasm-simd-threaded.wasm': '/assets/onnx/ort-wasm-simd-threaded.wasm',
};

export const sessionParams: SessionParameters = {
    numThreads: 0,
    executionProviders: ['cpu'],
    wasmRoot: wasmPaths,
};
