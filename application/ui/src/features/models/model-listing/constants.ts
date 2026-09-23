// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// `minmax(0, …)` lets columns shrink below their longest unbreakable word (e.g. TIMM ids).
export const GRID_COLUMNS = [
    [
        'minmax(0, 2fr)',
        'minmax(0, 1fr)',
        'minmax(0, 2fr)',
        'minmax(0, 1fr)',
        'minmax(0, 1fr)',
        'minmax(0, 1fr)',
        'minmax(auto, var(--spectrum-global-dimension-size-1000))',
    ].join(' '),
];
