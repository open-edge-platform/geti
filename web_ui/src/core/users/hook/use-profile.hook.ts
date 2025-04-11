// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { queryOptions, useSuspenseQuery } from '@tanstack/react-query';

import QUERY_KEYS from '../../../core/requests/query-keys';
import { useApplicationServices } from '../../../core/services/application-services-provider.component';
import { OnboardingService } from '../services/onboarding-service.interface';

export const profileQueryOptions = (onboardingService: OnboardingService) => {
    return queryOptions({
        queryKey: QUERY_KEYS.USER_ONBOARDING_PROFILE,
        queryFn: () => {
            return onboardingService.getActiveUserProfile();
        },
        // We set the cache time so that after the user's profile is fetched for the onboarding service,
        // we don't also fetch the user's profile when fetching their organization
        gcTime: 5 * 60 * 1000,
        retry: false,
    });
};

export const useProfileQuery = () => {
    const { onboardingService } = useApplicationServices();

    return useSuspenseQuery(profileQueryOptions(onboardingService));
};
