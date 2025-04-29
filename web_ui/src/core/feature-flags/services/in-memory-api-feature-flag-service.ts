// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DEV_FEATURE_FLAGS, FeatureFlags, FeatureFlagService } from './feature-flag-service.interface';

export const createInMemoryApiFeatureFlagService = (): FeatureFlagService => {
    const getFeatureFlags = async (): Promise<FeatureFlags> => Promise.resolve(DEV_FEATURE_FLAGS);

    return { getFeatureFlags };
};
