// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
