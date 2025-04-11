// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect } from '@playwright/test';

import { test } from '../../../fixtures/base-test';
import { notFoundHandler } from '../../../fixtures/open-api/setup-open-api-handlers';
import { generateToken } from '../../../utils/generate-token';

const PASSWORD = '@AHardPasswordToGuess';

test.describe('Registration', () => {
    test.beforeEach(async ({ page }) => {
        // Clear authentication storage to make sure to simulate that the user is not logged in
        await page.addInitScript(() => localStorage.clear());
    });

    test('it will let the user request to reset their password', async ({ page, openApi, baseURL }) => {
        openApi.registerHandler('notFound', (c, res, ctx) => {
            if (c.request.path === '/users/request_password_reset') {
                return res(ctx.status(200), ctx.json({ moi: 'houi' }));
            }

            return notFoundHandler(c, res, ctx);
        });

        await page.goto('/registration/forgot-password');

        await page.getByRole('textbox', { name: /email address/i }).fill('test@intel.com');

        await page.getByRole('button', { name: /reset/i }).click();

        await expect(
            page.getByText(/a message has been sent to your email with further instructions\./i)
        ).toBeVisible();

        await page.getByRole('link', { name: /sign in/i }).click();

        await expect(page).toHaveURL(`${baseURL}/`);
    });

    test('it will let the user reset their password', async ({ page, openApi, baseURL }) => {
        openApi.registerHandler('notFound', (c, res, ctx) => {
            if (c.request.path === '/users/reset_password') {
                return res(ctx.status(200), ctx.json({ moi: 'houi' }));
            }

            return notFoundHandler(c, res, ctx);
        });

        const token = await generateToken('2h', { mail: 'test@gmail.com' });

        await page.goto(`/registration/reset-password?token=${token}`);

        await page.getByLabel('New password', { exact: true }).fill(PASSWORD);
        await page.getByLabel('Confirm new password').fill(PASSWORD);
        await page.getByRole('button', { name: /submit/i }).click();

        await expect(async () => {
            await expect(page).toHaveURL(`${baseURL}/`);
        }).toPass();
    });

    test('Shows a user does not exist and redirects home', async ({ page, baseURL }) => {
        await page.goto(`/registration/users/not-found`);
        await expect(page.getByText(/User does not exist/)).toBeVisible();
        await page.getByRole('button').click();
        await expect(page).toHaveURL(`${baseURL}/`);
    });

    test('Shows a link does not exist and redirects home', async ({ page, baseURL }) => {
        await page.goto(`/registration/invalid-link`);
        await page.getByRole('button').click();
        await expect(page).toHaveURL(`${baseURL}/`);
    });

    test('Sign up a new user from an email invitation', async ({ page, openApi, baseURL }) => {
        openApi.registerHandler('notFound', (c, res, ctx) => {
            if (c.request.path === '/users/confirm_registration') {
                return res(ctx.status(200), ctx.json({ moi: 'houi' }));
            }

            return notFoundHandler(c, res, ctx);
        });

        const token = await generateToken('2h', { mail: 'test@gmail.com' });

        await page.goto(`/registration/sign-up?token=${token}`);

        await page.getByRole('textbox', { name: /first name/i }).fill('John');
        await page.getByRole('textbox', { name: /last name/i }).fill('Snow');

        await page.getByLabel('Password', { exact: true }).fill(PASSWORD);
        await page.getByLabel('Confirm password').fill(PASSWORD);

        await page.getByRole('button', { name: /sign up/i }).click();

        await expect(async () => {
            await expect(page).toHaveURL(`${baseURL}/`);
        }).toPass();
    });

    test('Invalid token', async ({ page }) => {
        await page.goto(`/registration/reset-password`);

        await expect(page.getByRole('alert')).toBeVisible();
        await expect(
            page.getByRole('heading', { name: 'Invitation token is required for further actions' })
        ).toBeVisible();
    });
});
