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

import { expect, test } from '../../fixtures/base-test';
import { ACCOUNT_URL } from './mocks';

const accountGeneralUrl = ACCOUNT_URL('5b1f89f3-aba5-4a5f-84ab-de9abb8e0633', 'profile');

const ORGANIZATION_ID = '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633';
const WORKSPACE_ID = '61011e42d891c82e13ec92da';
const getMockedUser = () => {
    return {
        id: '43fc5d9c-4db1-48e8-bebb-d625f6a5dadc',
        firstName: 'Gordon',
        secondName: 'Moore',
        email: 'admin@intel.com',
        externalId: '',
        country: '',
        status: 'ACT',
        organizationId: '14b951d9-8a7e-4fe8-870f-99c4abf0626e',
        organizationStatus: 'ACT',
        lastSuccessfulLogin: null,
        currentSuccessfulLogin: null,
        createdAt: null,
        createdBy: '',
        modifiedAt: null,
        modifiedBy: '',
        telemetryConsent: '',
        telemetryConsentAt: null,
        userConsent: '',
        userConsentAt: null,
        presignedUrl: '',
        roles: [
            { role: 'organization_admin', resourceType: 'organization', resourceId: ORGANIZATION_ID },
            { role: 'workspace_admin', resourceType: 'workspace', resourceId: WORKSPACE_ID },
        ],
    };
};

test.describe('Account page - general tab', () => {
    test.beforeEach(async ({ page, registerApiResponse }) => {
        const user = getMockedUser();
        registerApiResponse('User_get_active_user', (_, res, ctx) => {
            return res(ctx.json(user));
        });

        await page.goto(accountGeneralUrl);
    });

    test('Updating user profile info', async ({ page, registerApiResponse }) => {
        const user = getMockedUser();

        registerApiResponse('User_modify', (req, res, ctx) => {
            user.firstName = req.body.firstName ?? '';
            user.secondName = req.body.secondName ?? '';

            return res(ctx.status(200));
        });
        const userAvatarPlaceholder = page.locator('#page-layout-id').getByTestId('placeholder-avatar-id');
        await expect(userAvatarPlaceholder).toBeVisible();
        await expect(userAvatarPlaceholder.getByTestId('placeholder-letter-id')).toHaveText('G');

        const email = page.getByRole('textbox', { name: /email address/i });
        await expect(email).toBeVisible();
        await expect(email).toHaveValue('admin@intel.com');
        await expect(email).toHaveAttribute('readonly');

        const firstName = page.getByRole('textbox', { name: /first name/i });
        await expect(firstName).toBeVisible();
        await expect(firstName).toHaveValue('Gordon');

        const lastName = page.getByRole('textbox', { name: /last name/i });
        await expect(lastName).toBeVisible();
        await expect(lastName).toHaveValue('Moore');

        const save = page.getByRole('button', { name: 'Save' });
        await expect(save).toBeDisabled();

        await firstName.fill('Robert');
        await lastName.fill('Noyce');
        await save.click();

        await expect.poll(() => user.firstName).toEqual('Robert');
        expect(user.secondName).toEqual('Noyce');
    });

    test.describe('SaaS', () => {
        test.use({ isSaaS: true });

        test('SaaS profile', async ({ page }) => {
            const email = page.getByRole('textbox', { name: /email address/i });
            await expect(email).toBeVisible();
            await expect(email).toHaveValue('admin@intel.com');
            await expect(email).toHaveAttribute('readonly');

            await expect(page.getByRole('textbox', { name: /full name/i })).toHaveValue('Gordon Moore');

            await expect(page.getByRole('button', { name: 'Save' })).toBeHidden();
        });
    });
});
