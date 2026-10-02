// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sessionParams } from '@geti-ui/smart-tools/utils';

// WebView2 honours COEP credentialless so crossOriginIsolated is true, but
// emscripten's nested module workers never load in the Tauri webview — threaded
// ORT then blocks forever and blows SAM_DECODER_TIMEOUT_MS. Keep a single thread;
// WebGPU doesn't need the pthread pool, and ORT skips it when no adapter exists.
sessionParams.numThreads = 1;
sessionParams.executionProviders = ['webgpu', 'cpu'];
