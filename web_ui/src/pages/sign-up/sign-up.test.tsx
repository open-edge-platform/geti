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

import { screen } from '@testing-library/react';
import { useAuth } from 'react-oidc-context';

import { AccountStatus } from '../../core/organizations/organizations.interface';
import { createInMemoryOnboardingService } from '../../core/users/services/inmemory-onboarding-service';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { getMockedOrganizationMetadata } from '../../test-utils/mocked-items-factory/mocked-organization';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { SignUp } from './sign-up.component';

jest.mock('../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    useIsSaasEnv: jest.fn(() => true),
}));

const mockOnboardingToken = 'cool-token';
jest.mock('react-oidc-context', () => ({
    ...jest.requireActual('react-oidc-context'),
    useAuth: jest.fn(() => ({
        user: {
            url_state: mockOnboardingToken,
            profile: { isInternal: true },
        },
    })),
}));

jest.mock('jwt-decode', () => ({
    jwtDecode: jest.fn(),
}));

describe('SignUp', () => {
    describe('On SaaS', () => {
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.onboardUser = jest.fn();

        beforeAll(() => {
            jest.mocked(useIsSaasEnv).mockReturnValue(true);
        });

        beforeEach(() => {
            jest.clearAllMocks();

            jest.mocked(useAuth).mockReturnValue({
                user: {
                    url_state: mockOnboardingToken,
                    // @ts-expect-error we don't care about other properties of profile
                    profile: { isInternal: false },
                },
            });
        });

        it('Does not render the dialog if FEATURE_FLAG_USER_ONBOARDING is disabled', async () => {
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [
                        getMockedOrganizationMetadata({
                            status: AccountStatus.INVITED,
                            userStatus: AccountStatus.INVITED,
                        }),
                    ],
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            render(<SignUp>Content</SignUp>, {
                services: { onboardingService },
                featureFlags: { FEATURE_FLAG_USER_ONBOARDING: false },
            });

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        it('Does not render the dialog if the user has accepted terms and conditions', async () => {
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [
                        getMockedOrganizationMetadata({
                            status: AccountStatus.ACTIVATED,
                            userStatus: AccountStatus.ACTIVATED,
                        }),
                    ],
                    hasAcceptedUserTermsAndConditions: true,
                };
            };

            render(<SignUp>Content</SignUp>, {
                services: { onboardingService },
                featureFlags: { FEATURE_FLAG_USER_ONBOARDING: false },
            });

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });
    });

    describe('On Prem', () => {
        beforeAll(() => {
            jest.mocked(useIsSaasEnv).mockReturnValue(false);
        });

        it('Does not render the SignUp form, displays the children instead', async () => {
            render(<SignUp>Content</SignUp>, {
                featureFlags: { FEATURE_FLAG_USER_ONBOARDING: true },
            });

            expect(screen.getByText('Content')).toBeInTheDocument();
        });
    });
});
