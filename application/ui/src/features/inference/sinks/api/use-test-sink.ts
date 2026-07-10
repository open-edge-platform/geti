// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useQuery } from '@tanstack/react-query';

export const testSinkQueryOptions = (sinkId: string) =>
    $api.queryOptions(
        'post',
        '/api/sinks/{sink_id}:test',
        { params: { path: { sink_id: sinkId } } },
        { enabled: false, staleTime: Infinity }
    );

export const useTestSink = (sinkId: string) => {
    return useQuery(testSinkQueryOptions(sinkId));
};
