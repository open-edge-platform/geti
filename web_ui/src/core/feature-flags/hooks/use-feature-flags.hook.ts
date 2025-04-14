// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { FeatureFlags } from '../services/feature-flag-service.interface';
import { useFeatureFlagQuery } from './use-feature-flag-query.hook';

export const useFeatureFlags = () => {
    const { data: featureFlags } = useFeatureFlagQuery();

    const featureFlagsProxy = useMemo(() => {
        return new Proxy(featureFlags, {
            get: (featureFlagsObject: FeatureFlags, property: keyof FeatureFlags): boolean => {
                return featureFlagsObject[property] ?? false;
            },
        });
    }, [featureFlags]);

    return featureFlagsProxy;
};
