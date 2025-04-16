// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { AccountStatusDTO } from '../../../src/core/organizations/dtos/organizations.interface';
import { test } from '../../fixtures/base-test';

export const profileResponse = {
    organizations: [
        {
            organizationName: 'Organization 1',
            userStatus: AccountStatusDTO.ACTIVE,
            organizationStatus: AccountStatusDTO.ACTIVE,
            organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
            organizationCreatedAt: '2024-10-04T10:04:24Z',
        },
    ],
    telemetryConsent: 'y',
    telemetryConsentAt: '2023-11-02T10:03:47.428474Z',
    userConsent: null,
    userConsentAt: null,
};

test.describe('LicenseModal', () => {
    test.use({ isSaaS: false });

    test('Modal should be displayed automatically if the user did not consent', async ({
        page,
        registerApiResponse,
        licenseModalPage,
    }) => {
        let userConsent: string | null = null;

        registerApiResponse('User_get_user_profile', (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json({ ...profileResponse, userConsent }));
        });
        await page.goto('/');

        await expect(licenseModalPage.getLicenseAcceptButton()).toBeVisible();

        registerApiResponse('User_modify', (req, res, ctx) => {
            userConsent = req.body.userConsent || null;

            return res(ctx.status(200), ctx.json({ ...req.body, userConsent }));
        });

        await licenseModalPage.acceptLicense();

        await expect(licenseModalPage.getDialog()).toBeHidden();

        // Refresh the page
        await page.reload();

        await expect(licenseModalPage.getDialog()).toBeHidden();
    });

    test('About page - User should be able to consult license', async ({
        registerApiResponse,
        page,
        licenseModalPage,
    }) => {
        registerApiResponse('User_get_user_profile', (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json({ ...profileResponse, userConsent: 'y' }));
        });

        await page.goto('/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/about');

        await page.getByRole('button', { name: 'License' }).click();
        await expect(licenseModalPage.getDialog()).toBeVisible();

        await licenseModalPage.getLicenseCloseButton().click();
        await expect(licenseModalPage.getDialog()).toBeHidden();
    });
});
