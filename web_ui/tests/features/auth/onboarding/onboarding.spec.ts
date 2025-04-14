// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { AccountStatusDTO } from '../../../../src/core/organizations/dtos/organizations.interface';
import { API_URLS } from '../../../../src/core/services/urls';
import { expect, test } from '../../../fixtures/base-test';
import { notFoundHandler } from '../../../fixtures/open-api/setup-open-api-handlers';
import { OnboardingPage } from '../../../fixtures/page-objects/onboarding-page';
import { switchCallsAfter } from '../../../utils/api';
import { generateToken } from '../../../utils/generate-token';

const expectInvalidOrganizationsScreenToBeVisible = async (page: Page, onboardingPage: OnboardingPage) => {
    await expect(onboardingPage.getRegistrationHeading()).toBeHidden();

    await expect(page.getByRole('heading', { name: /access denied/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /request trial/i })).toBeVisible();
};

const getMockedProfile = ({
    organizationId,
    status = AccountStatusDTO.ACTIVE,
    userConsent = 'y',
}: {
    status?: AccountStatusDTO;
    userConsent?: string;
    organizationId: string;
}) => ({
    organizations: [
        {
            userStatus: status,
            organizationId,
            organizationName: 'Organization 1',
            organizationStatus: status,
            organizationCreatedAt: '2024-10-04T10:04:24Z',
        },
    ],
    telemetryConsent: null,
    telemetryConsentAt: null,
    userConsent,
});

test.describe('Onboarding', () => {
    const switchAfter = switchCallsAfter(1);
    const organizationId = 'test-organization-id';

    test.use({ isSaaS: true });

    test.describe('Invitation without free tier', () => {
        test.use({
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_FREE_TIER: false,
            },
        });

        test('User invitation flow', async ({ page, onboardingPage, registerApiResponse }) => {
            const getProfile = switchAfter([
                async (_, res, ctx) => {
                    return res(
                        ctx.json(
                            getMockedProfile({
                                userConsent: 'n',
                                organizationId,
                                status: AccountStatusDTO.REGISTERED,
                            })
                        )
                    );
                },
                async (_, res, ctx) => {
                    return res(
                        ctx.json(
                            getMockedProfile({
                                userConsent: 'y',
                                organizationId,
                                status: AccountStatusDTO.ACTIVE,
                            })
                        )
                    );
                },
            ]);
            registerApiResponse('User_get_user_profile', getProfile);

            await page.goto('/');

            await expect(onboardingPage.getRegistrationHeading()).toBeVisible();

            const submitButton = onboardingPage.getSubmitButton();
            await expect(submitButton).toBeDisabled();

            await onboardingPage.checkTermsAndConditions();

            await expect(submitButton).toBeEnabled();
            await onboardingPage.submit();

            await expect(page).toHaveURL(`/organizations/${organizationId}/workspaces/61011e42d891c82e13ec92da`);
        });

        test('User invitation flow without an invite', async ({ page, onboardingPage, registerApiResponse }) => {
            const getProfile = switchAfter([
                async (_, res, ctx) => {
                    return res(ctx.status(404));
                },
                async (_, res, ctx) => {
                    return res(
                        ctx.json(
                            getMockedProfile({
                                organizationId,
                                userConsent: 'y',
                                status: AccountStatusDTO.ACTIVE,
                            })
                        )
                    );
                },
            ]);
            registerApiResponse('User_get_user_profile', getProfile);

            await page.goto('/');

            await expectInvalidOrganizationsScreenToBeVisible(page, onboardingPage);
        });
    });

    test.describe('Request access flow', () => {
        test.use({
            featureFlags: {
                FEATURE_FLAG_USER_ONBOARDING: true,
                FEATURE_FLAG_REQ_ACCESS: true,
            },
        });

        test(
            'Onboards with the new request access flow only when there is no invitation token and profile returns ' +
                '404',
            async ({ registerApiResponse, page, onboardingPage, openApi }) => {
                let profile: ReturnType<typeof getMockedProfile> | null = null;

                registerApiResponse('User_get_user_profile', (_, res, ctx) => {
                    return res(profile === null ? ctx.status(404) : ctx.json(profile));
                });

                openApi.registerHandler('notFound', (context, res, ctx) => {
                    if (context.request.path.includes('/onboarding/user')) {
                        const newMemberRequest = structuredClone(context.request.body);
                        delete newMemberRequest.password;

                        profile = getMockedProfile({
                            userConsent: 'y',
                            organizationId,
                            status: AccountStatusDTO.REQUESTED_ACCESS,
                        });

                        return res(ctx.status(200), ctx.json({}));
                    }

                    return notFoundHandler(context, res, ctx);
                });

                await page.goto('/');

                await expect(onboardingPage.getRegistrationHeading()).toBeVisible();

                await onboardingPage.fillOrganizationName('My org');
                const requestAccessReason = 'Geti is just great';
                await onboardingPage.fillRequestAccessReason(requestAccessReason);

                await onboardingPage.checkTermsAndConditions();

                const onboardingRequestPromise = page.waitForRequest((req) =>
                    req.url().includes(API_URLS.USER_ONBOARDING)
                );

                await onboardingPage.submit();

                const onboardingRequest = await onboardingRequestPromise;
                const requestPayload = onboardingRequest.postDataJSON() ?? {};

                expect(requestPayload).toEqual(expect.objectContaining({ request_access_reason: requestAccessReason }));

                await expect(page).toHaveURL(`/requested-access`);
                await expect(onboardingPage.getRequestedAccessHeading()).toBeVisible();
                await expect(onboardingPage.getRequestAccessContent()).toBeVisible();
            }
        );

        test('Does not display request access flow when there is invitation token', async ({
            registerApiResponse,
            page,
            onboardingPage,
        }) => {
            const profile: ReturnType<typeof getMockedProfile> | null = null;

            const jwt = await generateToken();

            registerApiResponse('User_get_user_profile', (_, res, ctx) => {
                return res(profile === null ? ctx.status(404) : ctx.json(profile));
            });

            await page.goto(`?signup-token=${jwt}`);

            await expect(onboardingPage.getRegistrationHeading()).toBeVisible();

            await expect(onboardingPage.getRequestAccessReasonField()).toBeHidden();
            await expect(onboardingPage.getRequestAccessButton()).toBeHidden();
            await expect(onboardingPage.getSubmitButton()).toBeVisible();
        });

        test('Does not display request access flow when there is at least one organization', async ({
            registerApiResponse,
            page,
            onboardingPage,
        }) => {
            registerApiResponse('User_get_user_profile', (_, res, ctx) => {
                return res(
                    ctx.json(
                        getMockedProfile({
                            organizationId,
                            userConsent: 'n',
                            status: AccountStatusDTO.REGISTERED,
                        })
                    )
                );
            });

            await page.goto('/');

            await expect(onboardingPage.getRegistrationHeading()).toBeVisible();

            await expect(onboardingPage.getRequestAccessReasonField()).toBeHidden();
            await expect(onboardingPage.getRequestAccessButton()).toBeHidden();
            await expect(onboardingPage.getSubmitButton()).toBeVisible();
        });
    });

    test.describe('Free tier signup', () => {
        test.describe('FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK is enabled', () => {
            test.use({
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_FREE_TIER: true,
                    FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: true,
                },
            });

            test('Free tier invitation flow without organization and valid token', async ({
                page,
                registerApiResponse,
                onboardingPage,
            }) => {
                const jwt = await generateToken();

                const getProfile = switchAfter([
                    async (_, res, ctx) => {
                        return res(ctx.status(404));
                    },
                    async (_, res, ctx) => {
                        return res(
                            ctx.json(
                                getMockedProfile({
                                    organizationId,
                                    userConsent: 'y',
                                    status: AccountStatusDTO.ACTIVE,
                                })
                            )
                        );
                    },
                ]);

                registerApiResponse('User_get_user_profile', getProfile);

                await page.goto(`?signup-token=${jwt}`);

                await expect(onboardingPage.getRegistrationHeading()).toBeVisible();

                const submitButton = onboardingPage.getSubmitButton();
                await expect(submitButton).toBeDisabled();

                await onboardingPage.fillOrganizationName('My org');
                await onboardingPage.checkTermsAndConditions();

                await expect(submitButton).toBeEnabled();

                await onboardingPage.submit();

                await expect(page).toHaveURL(`/organizations/${organizationId}/workspaces/61011e42d891c82e13ec92da`);
            });

            test('Free tier invitation flow without organization and invalid token', async ({
                page,
                registerApiResponse,
                onboardingPage,
            }) => {
                const jwt = await generateToken('-2h');

                const getProfile = switchAfter([
                    async (_, res, ctx) => {
                        return res(ctx.status(404));
                    },
                    async (_, res, ctx) => {
                        return res(
                            ctx.json(
                                getMockedProfile({
                                    organizationId,
                                    userConsent: 'y',
                                    status: AccountStatusDTO.ACTIVE,
                                })
                            )
                        );
                    },
                ]);

                registerApiResponse('User_get_user_profile', getProfile);

                await page.goto(`?signup-token=${jwt}`);

                await expect(onboardingPage.getRegistrationHeading()).toBeVisible();

                const submitButton = onboardingPage.getSubmitButton();
                await expect(submitButton).toBeDisabled();

                await onboardingPage.fillOrganizationName('My org');
                await onboardingPage.checkTermsAndConditions();

                await expect(submitButton).toBeDisabled();

                await expect(onboardingPage.getInvalidTokenAlert()).toBeVisible();
            });

            test('Free tier invitation flow without organization and with malicious token', async ({
                page,
                openApi,
                onboardingPage,
                registerApiResponse,
            }) => {
                // We cannot check if token was malicious on the frontend, we rely on the backend response in this case
                const jwt = await generateToken();

                registerApiResponse('User_get_user_profile', async (_, res, ctx) => {
                    return res(ctx.status(404));
                });

                openApi.registerHandler('notFound', (c, res, ctx) => {
                    if (c.request.path === '/onboarding/user') {
                        return res(ctx.status(401), ctx.json({ detail: 'Invalid sign-up token' }));
                    }

                    return notFoundHandler(c, res, ctx);
                });

                await page.goto(`?signup-token=${jwt}`);

                await expect(onboardingPage.getRegistrationHeading()).toBeVisible();

                const submitButton = onboardingPage.getSubmitButton();
                await expect(submitButton).toBeDisabled();

                await onboardingPage.fillOrganizationName('My org');
                await onboardingPage.checkTermsAndConditions();

                await expect(submitButton).toBeEnabled();

                await onboardingPage.submit();

                await expectInvalidOrganizationsScreenToBeVisible(page, onboardingPage);
            });
        });

        test.describe('FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK is not enabled', () => {
            test.use({
                featureFlags: {
                    FEATURE_FLAG_USER_ONBOARDING: true,
                    FEATURE_FLAG_FREE_TIER: true,
                    FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: false,
                },
            });

            test('Free tier invitation flow with organization and without token', async ({
                page,
                registerApiResponse,
                onboardingPage,
            }) => {
                const getProfile = switchAfter([
                    async (_, res, ctx) => {
                        return res(
                            ctx.json(
                                getMockedProfile({
                                    organizationId,
                                    userConsent: 'n',
                                    status: AccountStatusDTO.REGISTERED,
                                })
                            )
                        );
                    },
                    async (_, res, ctx) => {
                        return res(
                            ctx.json(
                                getMockedProfile({
                                    organizationId,
                                    userConsent: 'y',
                                    status: AccountStatusDTO.ACTIVE,
                                })
                            )
                        );
                    },
                ]);

                registerApiResponse('User_get_user_profile', getProfile);

                await page.goto(`/`);

                await expect(onboardingPage.getRegistrationHeading()).toBeVisible();

                const submitButton = onboardingPage.getSubmitButton();
                await expect(submitButton).toBeDisabled();

                await onboardingPage.checkTermsAndConditions();

                await expect(submitButton).toBeEnabled();
                await onboardingPage.submit();

                await expect(page).toHaveURL(`/organizations/${organizationId}/workspaces/61011e42d891c82e13ec92da`);
            });
        });
    });
});
