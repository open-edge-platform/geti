// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { queryOptions, useSuspenseQuery } from '@tanstack/react-query';

import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { OnboardingService } from '../services/onboarding-service.interface';

const profileQueryOptions = (onboardingService: OnboardingService) => {
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
