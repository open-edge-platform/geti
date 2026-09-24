// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { DatasetSubset } from '@/api/types';

export const SUBSET_LABEL_KEYS = {
    training: 'common.labels.training',
    validation: 'common.labels.validation',
    testing: 'common.labels.testing',
    unassigned: 'common.labels.unassigned',
} as const satisfies Record<DatasetSubset, string>;

export const SUBSETS: DatasetSubset[] = ['training', 'validation', 'testing', 'unassigned'];
