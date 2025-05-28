// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { useApplicationServices } from '../../services/application-services-provider.component';
import { useProfileQuery } from './use-profile.hook';

interface OnboardUserMutationPayload {
    userConsentIsGiven: boolean;
    organizationId: string;
    userOrganizationName?: string;
    onboardingToken?: string | null;
    requestAccessReason?: string;
}

export const useOnboardUserMutation = () => {
    const { onboardingService } = useApplicationServices();
    const profileQuery = useProfileQuery();

    const onboardUserMutation = useMutation<void, AxiosError, OnboardUserMutationPayload>({
        mutationFn: ({
            userConsentIsGiven,
            organizationId,
            userOrganizationName,
            onboardingToken,
            requestAccessReason,
        }) => {
            return onboardingService.onboardUser({
                userConsentIsGiven,
                organizationId,
                requestAccessReason,
                organizationName: userOrganizationName,
                onboardingToken: onboardingToken ?? undefined,
            });
        },
        onSuccess: () => {
            profileQuery.refetch();
        },
    });

    return onboardUserMutation;
};
