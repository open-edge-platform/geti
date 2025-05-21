// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { client } from '@geti/core';
import { isAxiosError } from 'axios';

import { AccountStatusDTO } from '../../organizations/dtos/organizations.interface';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { is404Error } from '../../services/utils';
import { GenerateTokenDTO } from '../dtos/onboarding.interface';
import { OnboardingService } from './onboarding-service.interface';
import { USER_STATUS_MAPPING } from './utils';

interface ProfileDTO {
    organizations: Array<{
        organizationName: string;
        userStatus: AccountStatusDTO;
        organizationStatus: AccountStatusDTO;
        organizationId: string;
        organizationCreatedAt: string;
    }>;
    userConsent?: string;
    userConsentAt: string | null;
    telemetryConsentAt: string | null;
    telemetryConsent: string | null;
}

export const createApiOnboardingService: CreateApiService<OnboardingService> = (
    { instance, router } = { instance: client, router: API_URLS }
) => {
    const getActiveUserProfile: OnboardingService['getActiveUserProfile'] = async () => {
        try {
            const profile = await instance.get<ProfileDTO>(router.USER_PROFILE);

            return {
                ...profile.data,
                organizations: profile.data.organizations.map((organization) => ({
                    id: organization.organizationId,
                    name: organization.organizationName,
                    createdAt: organization.organizationCreatedAt,
                    status: USER_STATUS_MAPPING[organization.organizationStatus],
                    userStatus: USER_STATUS_MAPPING[organization.userStatus],
                })),
                hasAcceptedUserTermsAndConditions: profile.data.userConsent === 'y',
            };
        } catch (error) {
            if (isAxiosError(error) && !is404Error(error)) {
                throw error;
            }

            return {
                organizations: [],
                hasAcceptedUserTermsAndConditions: false,
            };
        }
    };

    const onboardUser: OnboardingService['onboardUser'] = async ({
        userConsentIsGiven,
        organizationId,
        organizationName,
        onboardingToken,
        requestAccessReason,
    }) => {
        return instance.post(router.USER_ONBOARDING, {
            user_consent: userConsentIsGiven ? 'y' : 'no',
            telemetry_consent: userConsentIsGiven ? 'y' : 'no',
            organization_id: organizationId,
            organization_name: organizationName,
            onboarding_token: onboardingToken,
            request_access_reason: requestAccessReason,
        });
    };

    const generateToken: OnboardingService['generateToken'] = async ({ dateFrom, dateTo }) => {
        const { data } = await instance.post<GenerateTokenDTO>(router.GENERATE_ONBOARDING_TOKEN, {
            date_to: dateTo,
            date_from: dateFrom,
        });

        return {
            onboardingToken: data.onboarding_token,
        };
    };

    return {
        getActiveUserProfile,
        onboardUser,
        generateToken,
    };
};
