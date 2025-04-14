// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import path from 'path';

import { mergeTests } from '@playwright/test';
import dotenv from 'dotenv';

import { annotatorTest as baseTest } from './../fixtures/annotator-test';
import { test as apiTest } from './api-fixtures';

dotenv.config({ path: path.resolve(__dirname, '.env') });

const test = mergeTests(apiTest, baseTest).extend<{
    account: { email: string; password: string };
}>({
    account: async ({}, use) => {
        const email = process.env.PW_E2E_EMAIL ?? '';
        const password = process.env.PW_E2E_PASSWORD ?? '';

        await use({ email, password });
    },
    page: async ({ page }, use) => {
        await page.addLocatorHandler(
            page.getByRole('button', { name: 'Open to dismiss all help dialogs' }),
            async (menu) => {
                await menu.click();
                await page.getByText('Dismiss all').click();
            },
            { times: 1 }
        );

        await use(page);

        // Update the authentication storage so that it updates the access and refresh tokens
        const authFile = path.join(__dirname, '.auth/user.json');
        await page.context().storageState({ path: authFile });
    },
    setupOpenAPIServer: async ({}, use) => {
        // Overwrite the openapi fixture so that we don't use any of the OpenAPI backend's mocks
        await use(undefined);
    },
    // Overwrite the storage state set by testWithLocalStorageState
    storageState: async ({}, use) => {
        const authFile = path.join(__dirname, '.auth/user.json');

        await use(authFile);
    },
    ignoreHTTPSErrors: true,
    baseURL: process.env.PW_E2E_PLATFORM,
});

export { test };
