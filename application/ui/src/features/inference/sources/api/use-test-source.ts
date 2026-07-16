// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useQuery } from '@tanstack/react-query';

export const testSourceQueryOptions = (sourceId: string) =>
    $api.queryOptions(
        'post',
        '/api/sources/{source_id}:test',
        { params: { path: { source_id: sourceId } } },
        { enabled: false, staleTime: Infinity }
    );

export const useTestSource = (sourceId: string) => {
    return useQuery(testSourceQueryOptions(sourceId));
};
