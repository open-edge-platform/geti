// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { PipelineHealth, PipelineStatus } from '@/api/types';

export const getMockedStatus = (customStatus?: Partial<PipelineStatus>): PipelineStatus => {
    return {
        status: 'ok',
        updated_at: '2026-01-01T00:00:00Z',
        message: null,
        ...customStatus,
    };
};

export const getMockedPipelineHealth = (customHealth?: Partial<PipelineHealth>): PipelineHealth => {
    return {
        status: 'running',
        components: {
            source: getMockedStatus(),
            sink: getMockedStatus(),
            model: getMockedStatus(),
        },
        ...customHealth,
    };
};
