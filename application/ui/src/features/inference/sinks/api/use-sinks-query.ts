// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { usePrefetchQuery, useSuspenseQuery } from '@tanstack/react-query';

const sinksQueryOptions = () => {
    return $api.queryOptions('get', '/api/sinks');
};

export const usePrefetchSinksQuery = () => {
    usePrefetchQuery(sinksQueryOptions());
};

export const useSinksQuery = () => {
    return useSuspenseQuery(sinksQueryOptions());
};
