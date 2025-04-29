// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
