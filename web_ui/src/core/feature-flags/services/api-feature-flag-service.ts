// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { FeatureFlags, FeatureFlagService } from './feature-flag-service.interface';

export const createApiFeatureFlagService: CreateApiService<FeatureFlagService> = (
    { instance: platformInstance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getFeatureFlags = async (): Promise<FeatureFlags> => {
        const { data } = await platformInstance.get<FeatureFlags>(router.FEATURE_FLAGS);

        return data;
    };

    return { getFeatureFlags };
};
