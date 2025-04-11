// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
