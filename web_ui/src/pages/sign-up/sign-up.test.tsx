// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createInMemoryOnboardingService } from '@geti/core/src/users/services/inmemory-onboarding-service';
import { screen } from '@testing-library/react';
import { useAuth } from 'react-oidc-context';

import { AccountStatus } from '../../core/organizations/organizations.interface';
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
