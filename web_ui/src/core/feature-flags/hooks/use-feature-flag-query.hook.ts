// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useSuspenseQuery, UseSuspenseQueryOptions, UseSuspenseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import isEmpty from 'lodash/isEmpty';

import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { FeatureFlags, FeatureFlagService } from '../services/feature-flag-service.interface';

export const featureFlagQueryOptions = (
    featureFlagService: FeatureFlagService
): UseSuspenseQueryOptions<FeatureFlags, AxiosError> => {
    return {
        queryKey: QUERY_KEYS.FEATURE_FLAGS,
        queryFn: async () => {
            const data = await featureFlagService.getFeatureFlags();

            if (data && isEmpty(Object.keys(data))) {
                console.warn('Feature flag object is empty.');
            }

            return data;
        },
        retry: 0,
        staleTime: Infinity,
        gcTime: 10 * 1000,
    };
};

export const useFeatureFlagQuery = (): UseSuspenseQueryResult<FeatureFlags, AxiosError> => {
    const { featureFlagService } = useApplicationServices();

    return useSuspenseQuery<FeatureFlags, AxiosError>(featureFlagQueryOptions(featureFlagService));
};
