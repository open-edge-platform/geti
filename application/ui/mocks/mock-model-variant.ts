// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ModelVariant } from '@/api/types';

export const getMockedVariant = (overrides: Partial<ModelVariant> = {}): ModelVariant => ({
    id: 'variant-id',
    format: 'openvino',
    precision: 'fp16',
    weights_size: 1024,
    evaluations: [],
    files_deleted: false,
    optimal_confidence_threshold: 0.65,
    ...overrides,
});
