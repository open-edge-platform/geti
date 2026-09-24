// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DatasetView } from '@/api/types';

export const getMockedDatasetView = (overrides?: Partial<DatasetView>): DatasetView => {
    return {
        id: 'collection-one',
        name: 'Collection One',
        created_at: '',
        project_id: 'project-id',
        ...overrides,
    };
};
