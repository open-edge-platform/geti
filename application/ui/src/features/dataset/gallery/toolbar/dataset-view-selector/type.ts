// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DatasetView as DatasetViewSpec } from '@/api/types';

export type DatasetView = Pick<DatasetViewSpec, 'id' | 'name'>;
