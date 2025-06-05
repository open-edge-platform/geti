// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { createInMemoryOnboardingService } from '@geti/core/src/users/services/inmemory-onboarding-service';
import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import { HttpStatusCode } from 'axios';
import dayjs from 'dayjs';
import { jwtDecode } from 'jwt-decode';
import { useAuth } from 'react-oidc-context';
import { useParams } from 'react-router-dom';

import { AccountStatus } from '../../core/organizations/organizations.interface';
import { getMockedOrganizationMetadata } from '../../test-utils/mocked-items-factory/mocked-organization';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { SignUpOnSaas } from './sign-up-on-saas.component';

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(() => mockedNavigate),
    useParams: jest.fn(() => ({
        projectId: '123',
        workspaceId: '12345',
        organizationId: 'cf5da836-1071-45ce-882a-dde5d3a9e167',
    })),
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

describe('SignUpOnSaas', () => {
    const onboardingService = createInMemoryOnboardingService();
    onboardingService.onboardUser = jest.fn();

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

    it('displays Access denied screen when FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK is enabled and token in the invitation token is malicious', async () => {
        jest.mocked(useAuth).mockReturnValue({
            user: {
                url_state: 'token',
                // @ts-expect-error we don't care about other properties of profile
                profile: { isInternal: false },
            },
        });

        const today = dayjs();
        const expiredAt = today.add(1, 'day');
        const issuedAt = today.subtract(1, 'day');

        jest.mocked(jwtDecode).mockReturnValue({
            exp: expiredAt.unix(),
            iat: issuedAt.unix(),
        });

        onboardingService.onboardUser = () => {
            return Promise.reject({
                response: {
                    status: HttpStatusCode.Unauthorized,
                    data: { detail: 'Invalid sign-up token' },
                },
            });
        };

        onboardingService.getActiveUserProfile = async () => {
            return {
                organizations: [],
                hasAcceptedUserTermsAndConditions: false,
            };
        };

        render(<SignUpOnSaas />, {
            services: { onboardingService },
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_FREE_TIER: true,
                FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: true,
                FEATURE_FLAG_REQ_ACCESS: false,
            },
            profile: null,
        });

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        fireEvent.click(screen.getByRole('checkbox'));
        fireEvent.change(screen.getByTestId('organization-name-input'), { target: { value: 'My org' } });

        expect(screen.getByRole('button', { name: 'Submit' })).toBeEnabled();
        fireEvent.click(screen.getByRole('button', { name: 'Submit' }));

        expect(await screen.findByRole('heading', { name: 'Access denied' })).toBeInTheDocument();
        expect(screen.getByText(/You do not have access to any Intel Geti organization./)).toBeInTheDocument();
    });

    it('displays Access denied screen when FEATURE_FLAG_FREE_TIER is not enabled and there is no organization', async () => {
        jest.mocked(useAuth).mockReturnValue({
            user: {
                url_state: undefined,
                // @ts-expect-error we don't care about other properties of profile
                profile: { isInternal: false },
            },
        });

        onboardingService.getActiveUserProfile = async () => {
            return {
                organizations: [],
                hasAcceptedUserTermsAndConditions: false,
            };
        };

        render(<SignUpOnSaas />, {
            services: { onboardingService },
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_FREE_TIER: false,
                FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: false,
                FEATURE_FLAG_REQ_ACCESS: false,
            },
            profile: null,
        });

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.getByRole('heading', { name: 'Access denied' })).toBeInTheDocument();
        expect(screen.getByText(/You do not have access to any Intel Geti organization./)).toBeInTheDocument();
    });

    it('does not display Access denied screen when FEATURE_FLAG_FREE_TIER is not enabled, there is no organization and FEATURE_FLAG_REQ_ACCESS is enabled', async () => {
        jest.mocked(useAuth).mockReturnValue({
            user: {
                url_state: undefined,
                // @ts-expect-error we don't care about other properties of profile
                profile: { isInternal: false },
            },
        });

        onboardingService.getActiveUserProfile = async () => {
            return {
                organizations: [],
                hasAcceptedUserTermsAndConditions: false,
            };
        };

        render(<SignUpOnSaas />, {
            services: { onboardingService },
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_FREE_TIER: false,
                FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: false,
                FEATURE_FLAG_REQ_ACCESS: true,
            },
            profile: null,
        });

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(
            screen.getByRole('textbox', { name: /for what use case do you plan to use intel® geti™\?/i })
        ).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Request access' })).toBeInTheDocument();

        expect(screen.queryByRole('heading', { name: 'Access denied' })).not.toBeInTheDocument();
        expect(screen.queryByText(/You do not have access to any Intel Geti organization./)).not.toBeInTheDocument();
    });

    it('sends correct payload without onboarding token for internal intel user', async () => {
        jest.mocked(useParams).mockReturnValue({ organizationId: undefined });
        const mockOnboardUser = jest.fn();
        onboardingService.getActiveUserProfile = async () => {
            return {
                organizations: [],
                hasAcceptedUserTermsAndConditions: false,
            };
        };
        onboardingService.onboardUser = mockOnboardUser;
        jest.mocked(useAuth).mockReturnValue({
            user: {
                url_state: undefined,
                // @ts-expect-error we don't care about other properties of profile
                profile: { isInternal: true },
            },
        });

        render(<SignUpOnSaas />, {
            services: { onboardingService },
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_FREE_TIER: true,
                FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: true,
            },
            profile: null,
        });

        const submitButton = await screen.findByRole('button', { name: 'Submit' });
        expect(submitButton).toBeDisabled();

        fireEvent.click(screen.getByRole('checkbox'));
        fireEvent.change(screen.getByTestId('organization-name-input'), { target: { value: 'My org' } });

        expect(submitButton).toBeEnabled();
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(mockOnboardUser).toHaveBeenCalledWith({
                userConsentIsGiven: true,
                organizationId: '',

                organizationName: 'My org',
                onboardingToken: undefined,
            });
        });

        expect(mockedNavigate).not.toHaveBeenCalled();
    });

    it('sends correct payload with onboarding token for external user with valid token', async () => {
        jest.mocked(useParams).mockReturnValue({ organizationId: undefined });
        const mockOnboardUser = jest.fn();
        onboardingService.getActiveUserProfile = async () => {
            return {
                organizations: [],
                hasAcceptedUserTermsAndConditions: false,
            };
        };
        onboardingService.onboardUser = mockOnboardUser;

        const today = dayjs();
        const expiredAt = today.add(1, 'day');
        const issuedAt = today.subtract(1, 'day');

        jest.mocked(jwtDecode).mockReturnValue({
            exp: expiredAt.unix(),
            iat: issuedAt.unix(),
        });

        render(<SignUpOnSaas />, {
            services: { onboardingService },
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_FREE_TIER: true,
                FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: true,
            },
            profile: null,
        });

        const submitButton = await screen.findByRole('button', { name: 'Submit' });
        expect(submitButton).toBeDisabled();

        fireEvent.click(screen.getByRole('checkbox'));
        fireEvent.change(screen.getByTestId('organization-name-input'), { target: { value: 'My org' } });

        expect(submitButton).toBeEnabled();
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(mockOnboardUser).toHaveBeenCalledWith({
                userConsentIsGiven: true,
                organizationId: '',

                organizationName: 'My org',
                onboardingToken: mockOnboardingToken,
            });
        });

        expect(mockedNavigate).not.toHaveBeenCalled();
    });

    it('does not send request for external user with invalid token and show error alert', async () => {
        const mockOnboardUser = jest.fn();
        onboardingService.getActiveUserProfile = async () => {
            return {
                organizations: [],
                hasAcceptedUserTermsAndConditions: false,
            };
        };
        onboardingService.onboardUser = mockOnboardUser;

        const today = dayjs();
        const expiredAt = today.subtract(1, 'day');
        const issuedAt = today.subtract(2, 'day');

        jest.mocked(jwtDecode).mockReturnValue({
            exp: expiredAt.unix(),
            iat: issuedAt.unix(),
        });

        render(<SignUpOnSaas />, {
            services: { onboardingService },
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_FREE_TIER: true,
                FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: true,
            },
            profile: null,
        });

        const submitButton = await screen.findByRole('button', { name: 'Submit' });
        expect(submitButton).toBeDisabled();

        expect(mockOnboardUser).not.toHaveBeenCalled();

        expect(await screen.findByRole('alert')).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Your invitation link has expired' })).toBeInTheDocument();
    });

    it('does not require token to onboard when FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK is not enabled', async () => {
        jest.mocked(useAuth).mockReturnValue({
            user: {
                url_state: undefined,
                // @ts-expect-error we don't care about other properties of profile
                profile: { isInternal: false },
            },
        });
        const mockOnboardUser = jest.fn();
        onboardingService.onboardUser = mockOnboardUser;

        onboardingService.getActiveUserProfile = async () => {
            return {
                organizations: [],
                hasAcceptedUserTermsAndConditions: false,
            };
        };

        render(<SignUpOnSaas />, {
            services: { onboardingService },
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_FREE_TIER: true,
                FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: false,
            },
            profile: null,
        });

        const submitButton = await screen.findByRole('button', { name: 'Submit' });
        expect(submitButton).toBeDisabled();

        fireEvent.click(screen.getByRole('checkbox'));
        fireEvent.change(screen.getByTestId('organization-name-input'), { target: { value: 'My org' } });

        expect(submitButton).toBeEnabled();
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(mockOnboardUser).toHaveBeenCalledWith({
                userConsentIsGiven: true,
                organizationId: '',

                organizationName: 'My org',
                onboardingToken: undefined,
            });
        });
    });

    describe('additional fields', () => {
        const today = dayjs();
        const expiredAt = today.add(1, 'day');
        const issuedAt = today.subtract(1, 'day');

        beforeEach(() => {
            jest.mocked(jwtDecode).mockReturnValue({
                exp: expiredAt.unix(),
                iat: issuedAt.unix(),
            });
        });

        it('shows request access reason text field when FEATURE_FLAG_REQ_ACCESS is enabled, there are no organizations (profile endpoint returns 404) and there is no invitation token', async () => {
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [],
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            jest.mocked(useAuth).mockReturnValue({
                user: {
                    url_state: undefined,
                    // @ts-expect-error we don't care about other properties of profile
                    profile: { isInternal: false },
                },
            });

            render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_FREE_TIER: true,
                    FEATURE_FLAG_REQ_ACCESS: true,
                },
                profile: null,
            });

            await waitForElementToBeRemoved(screen.getByRole('progressbar'));

            expect(
                screen.getByRole('textbox', { name: /for what use case do you plan to use intel® geti™\?/i })
            ).toBeInTheDocument();
        });

        it('does not show request access reason text field when FEATURE_FLAG_REQ_ACCESS is enabled but there is already an organization', async () => {
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [getMockedOrganizationMetadata()],
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_FREE_TIER: true,
                    FEATURE_FLAG_REQ_ACCESS: true,
                },
                profile: null,
            });

            await waitForElementToBeRemoved(screen.getByRole('progressbar'));

            expect(
                screen.queryByRole('textbox', { name: /for what use case do you plan to use intel® geti™\?/i })
            ).not.toBeInTheDocument();
        });

        it('does not show request access reason text field when FEATURE_FLAG_REQ_ACCESS is enabled but there is an invitation token', async () => {
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [],
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            jest.mocked(useAuth).mockReturnValue({
                user: {
                    url_state: mockOnboardingToken,
                    // @ts-expect-error we don't care about other properties of profile
                    profile: { isInternal: false },
                },
            });

            render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_FREE_TIER: true,
                    FEATURE_FLAG_REQ_ACCESS: true,
                },
                profile: null,
            });

            await waitForElementToBeRemoved(screen.getByRole('progressbar'));

            expect(
                screen.queryByRole('textbox', { name: /for what use case do you plan to use intel® geti™\?/i })
            ).not.toBeInTheDocument();
        });

        it('does not show request access reason text field when FEATURE_FLAG_REQ_ACCESS is disabled', async () => {
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [],
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_FREE_TIER: true,
                    FEATURE_FLAG_REQ_ACCESS: false,
                },
                profile: null,
            });

            await waitForElementToBeRemoved(screen.getByRole('progressbar'));

            expect(
                screen.queryByRole('textbox', { name: /for what use case do you plan to use intel® geti™\?/i })
            ).not.toBeInTheDocument();
        });

        it('shows "organization name" field if the user does not exist and FEATURE_FLAG_FREE_TIER is enabled', async () => {
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [],
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            const { unmount } = render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_FREE_TIER: true,
                },
                profile: null,
            });

            await waitFor(() => {
                expect(screen.getByTestId('organization-name-input')).toBeInTheDocument();
            });

            unmount();

            render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_FREE_TIER: false,
                },
                profile: null,
            });

            expect(screen.queryByTestId('organization-name-input')).not.toBeInTheDocument();
        });

        it('shows "organization name" field if the user does not exist and FEATURE_FLAG_REQ_ACCESS is enabled', async () => {
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [],
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            const { unmount } = render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_REQ_ACCESS: true,
                },
                profile: null,
            });

            await waitFor(() => {
                expect(screen.getByTestId('organization-name-input')).toBeInTheDocument();
            });

            unmount();

            render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_REQ_ACCESS: false,
                },
                profile: null,
            });

            expect(screen.queryByTestId('organization-name-input')).not.toBeInTheDocument();
        });

        it('shows "organization" selection if the user does not exist and has multiple organization invitations', async () => {
            const organizations = [
                getMockedOrganizationMetadata({
                    name: 'invitation 1',
                    status: AccountStatus.INVITED,
                    userStatus: AccountStatus.INVITED,
                }),
                getMockedOrganizationMetadata({
                    id: '222',
                    name: 'invitation 2',
                    status: AccountStatus.ACTIVATED,
                    userStatus: AccountStatus.INVITED,
                }),
            ];
            const mockOnboardUser = jest.fn();
            onboardingService.onboardUser = mockOnboardUser;
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations,
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: { FEATURE_FLAG_USER_ONBOARDING: true },
                profile: null,
            });

            expect(await screen.findByRole('button', { name: 'Submit' })).toBeDisabled();

            fireEvent.click(screen.getByRole('checkbox'));
            expect(await screen.findByRole('button', { name: 'Submit' })).toBeDisabled();

            fireEvent.click(screen.getByRole('button', { name: /visible organizations/i }));
            fireEvent.click(screen.getByRole('option', { name: organizations[0].name }));

            fireEvent.click(await screen.findByRole('button', { name: 'Submit' }));

            await waitFor(() => {
                expect(mockOnboardUser).toHaveBeenCalledWith({
                    userConsentIsGiven: true,
                    organizationId: organizations[0].id,
                    onboardingToken: undefined,
                    organizationName: undefined,
                });
            });

            expect(mockedNavigate).toHaveBeenCalledWith(
                paths.organization.index({ organizationId: organizations[0].id })
            );
        });

        it('the organization is automatically selected if there is only one available option', async () => {
            const mockOnboardUser = jest.fn();
            const organization = getMockedOrganizationMetadata({
                id: '222',
                name: 'invitation 2',
                status: AccountStatus.ACTIVATED,
                userStatus: AccountStatus.INVITED,
            });

            onboardingService.onboardUser = mockOnboardUser;
            onboardingService.getActiveUserProfile = async () => {
                return {
                    organizations: [organization],
                    hasAcceptedUserTermsAndConditions: false,
                };
            };

            render(<SignUpOnSaas />, {
                services: { onboardingService },
                featureFlags: { FEATURE_FLAG_USER_ONBOARDING: true },
                profile: null,
            });

            await waitForElementToBeRemoved(screen.getByRole('progressbar'));

            expect(screen.getByText('Organization to onboard')).toBeVisible();

            const textBoxSelector = screen.getByRole('textbox', {
                name: /visible organization Organization to onboard/i,
            });

            expect(textBoxSelector).toBeVisible();
            expect(textBoxSelector).toHaveAttribute('readonly');
            expect(textBoxSelector).toHaveAttribute('value', organization.name);

            fireEvent.click(screen.getByRole('checkbox'));

            const submitButton = await screen.findByRole('button', { name: 'Submit' });
            expect(submitButton).toBeEnabled();

            fireEvent.click(submitButton);

            await waitFor(() => {
                expect(mockOnboardUser).toHaveBeenCalledWith({
                    userConsentIsGiven: true,
                    organizationId: organization.id,
                    onboardingToken: undefined,
                    organizationName: undefined,
                });
            });

            expect(mockedNavigate).toHaveBeenCalledWith(paths.organization.index({ organizationId: organization.id }));
        });
    });
});
