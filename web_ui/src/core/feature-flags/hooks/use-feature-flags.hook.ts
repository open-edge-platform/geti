// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
