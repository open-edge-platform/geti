// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Fixed size for multi-step/workflow dialogs so they don't resize between steps,
// capped so they don't grow excessively on large screens.
export const LARGE_DIALOG_SIZE = {
    width: 'min(85vw, 1400px)',
    height: 'min(85vh, 1000px)',
} as const;
