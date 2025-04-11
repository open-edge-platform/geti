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

import { AccountStatus } from '../../organizations/organizations.interface';

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
