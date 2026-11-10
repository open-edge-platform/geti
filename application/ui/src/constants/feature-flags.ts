// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const FEATURE_FLAGS = {
    SSIM_TOOL: true,
    // Serves fake OME images from a mock service worker (web only, not Tauri)
    // TODO(#7810): delete once the OME backend is merged, together with `startOmeDemo` in index.tsx
    OME_DEMO: true,
};
