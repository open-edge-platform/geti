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

import { Page } from '@playwright/test';

import { expect, test } from '../../fixtures/base-test';
import { ACCOUNT_URL } from './mocks';

test.describe('Account page - security tab', () => {
    const accountSecurityUrl = ACCOUNT_URL('5b1f89f3-aba5-4a5f-84ab-de9abb8e0633', 'security');

    const fillInput = async (id: string, text: string, page: Page) => {
        await page.locator(`#${id}`).click();
        //Note: it's needed for 'slower down' the test, without waiting for focus it puts all values to the last input
        await expect(page.locator(`#${id}`)).toBeFocused();
        await page.locator(`#${id}`).fill(text);
    };

    test.beforeEach(async ({ page }) => {
        await page.goto(accountSecurityUrl);
    });

    test('Check tab elements', async ({ page }) => {
        await expect(page.locator('#password-title')).toHaveText('Password');
        await expect(page.locator('#change-password-description')).toHaveText(
            'Set a unique password to protect your personal Intel® Geti™ account.'
        );

        await expect(page.getByRole('button', { name: 'Change password' })).toBeEnabled();
    });

    test('Check change password modal', async ({ page, registerApiResponse }) => {
        let storedPassword: string | null = null;
        registerApiResponse('update_user_password_users__user_id__update_password_post', (req, res, ctx) => {
            storedPassword = req.body.new_password;
            expect(req.body.old_password).toEqual('b2xkcGFzcw==');
            return res(ctx.status(200));
        });

        await page.getByRole('button', { name: 'Change password' }).click();
        const modal = page.getByTestId('modal');
        await expect(modal).toBeVisible();

        await expect(modal.locator('h2')).toHaveText('Change password');
        await expect(modal.getByRole('button', { name: 'Cancel' })).toBeEnabled();
        await expect(modal.getByRole('button', { name: 'Save' })).toBeDisabled();

        const newPass = 'This_is_a_decently_strong_password!@1';
        await fillInput('old-password', 'oldpass', page);
        await fillInput('new-password', newPass, page);
        await fillInput('confirm-password', newPass, page);

        await expect(modal.getByRole('button', { name: 'Save' })).toBeEnabled();
        await modal.getByRole('button', { name: 'Save' }).click();

        await expect.poll(() => storedPassword).toEqual('VGhpc19pc19hX2RlY2VudGx5X3N0cm9uZ19wYXNzd29yZCFAMQ==');
    });
});
