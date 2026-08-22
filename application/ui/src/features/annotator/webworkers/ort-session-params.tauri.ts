// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sessionParams } from '@geti-ui/smart-tools/utils';

// WebView2 honours COEP credentialless so crossOriginIsolated is true, but
// emscripten's nested module workers never load in the Tauri webview — threaded
// ORT then blocks forever and blows SAM_DECODER_TIMEOUT_MS.
sessionParams.numThreads = 1;
sessionParams.executionProviders = ['cpu'];
