// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

export class LoginPage {
    constructor(private page: Page) {}

    async login(email: string, password: string) {
        await this.page.addLocatorHandler(this.page.getByRole('button', { name: 'Deactivate Cookies' }), async () => {
            await this.page.getByRole('button', { name: 'Deactivate Cookies' }).click();
        });

        const dexEmail = this.page.getByLabel('Email address');
        const ciDaasEmail = this.page.getByPlaceholder('Email');
        const emailField = dexEmail.or(ciDaasEmail);

        // The initial page load may take some time due to us having to load both the
        // geti app and dex/cidaas over the Intel network
        await expect(emailField).toBeVisible({ timeout: 60_000 });
        await emailField.fill(email);

        // If sign in form for DEX is visible, use its form
        if (await dexEmail.isVisible()) {
            await this.page.getByLabel('Password').fill(password);
            await this.page.getByRole('button').click();
        }

        // If sign in form for CIDaaS is visible, use its form
        if (await ciDaasEmail.isVisible()) {
            await this.page.getByRole('button', { name: 'Next' }).click();

            await this.page.getByLabel('Password').fill(password);
            await this.page.getByRole('button', { name: 'Sign In' }).click();
        }

        await expect(this.page.getByLabel('intel geti').getByRole('img')).toBeVisible();
    }
}
