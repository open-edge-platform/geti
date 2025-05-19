// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useSuspenseQuery, UseSuspenseQueryOptions, UseSuspenseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isEmpty } from 'lodash-es';

import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { FeatureFlags, FeatureFlagService } from '../services/feature-flag-service.interface';

const featureFlagQueryOptions = (
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
