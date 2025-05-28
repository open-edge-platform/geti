// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AccountStatus } from '../../../../../src/core/organizations/organizations.interface';

export interface OrganizationMetadata {
    id: string;
    name: string;
    status: AccountStatus;
    createdAt: string;
    userStatus: AccountStatus;
}

export interface OnboardingProfile {
    organizations: OrganizationMetadata[];
    hasAcceptedUserTermsAndConditions: boolean;
}

export interface GenerateOnboardingTokenResponse {
    onboardingToken: string;
}

export interface GenerateOnboardingTokenParams {
    dateFrom: string;
    dateTo: string;
}

export interface OnboardingService {
    getActiveUserProfile: () => Promise<OnboardingProfile>;
    onboardUser: (options: {
        userConsentIsGiven: boolean;
        organizationId: string;
        organizationName?: string;
        onboardingToken?: string;
        requestAccessReason?: string;
    }) => Promise<void>;
    generateToken: (params: GenerateOnboardingTokenParams) => Promise<GenerateOnboardingTokenResponse>;
}
