// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { usePrefetchQuery, useSuspenseQuery } from '@tanstack/react-query';

const getTrainingDevicesQueryOptions = () => {
    return $api.queryOptions('get', '/api/system/devices/training');
};

export const useGetTrainingDevices = () => {
    return useSuspenseQuery(getTrainingDevicesQueryOptions());
};

export const usePrefetchTrainingDevices = () => {
    return usePrefetchQuery(getTrainingDevicesQueryOptions());
};
