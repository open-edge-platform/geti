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
import { OnboardingService } from './onboarding-service.interface';

export const createInMemoryOnboardingService = (): OnboardingService => {
    const getActiveUserProfile = async () => {
        return {
            organizations: [
                {
                    id: 'cf5da836-1071-45ce-882a-dde5d3a9e167',
                    name: 'organization name',
                    userStatus: AccountStatus.ACTIVATED,
                    status: AccountStatus.ACTIVATED,
                    createdAt: '2024-09-11T09:13:57Z',
                },
            ],
            hasAcceptedUserTermsAndConditions: true,
        };
    };

    const onboardUser = async () => {
        // TODO
    };

    const generateToken: OnboardingService['generateToken'] = () => {
        return Promise.resolve({ onboardingToken: 'test' });
    };

    return {
        onboardUser,
        generateToken,
        getActiveUserProfile,
    };
};
