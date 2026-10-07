// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, http, test } from '../fixtures';

test.describe('License agreement (web)', () => {
    test('shows the Ultralytics and optional DINOv3 licenses and accepts them', async ({ page, network }) => {
        let licenseAccepted = false;

        network.use(
            http.get('/api/system/info', ({ response }) => {
                return response(200).json({
                    license_accepted: licenseAccepted,
                    platform: 'linux',
                });
            }),
            http.post('/api/license/accept', ({ response }) => {
                licenseAccepted = true;

                return response(200).json({ license_accepted: true });
            }),
            http.get('/api/projects', ({ response }) => {
                return response(200).json([]);
            })
        );

        await page.goto('/');

        await expect(page.getByRole('heading', { name: 'License Agreements' })).toBeVisible();
        await expect(page.getByText('1 of 2')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Ultralytics AGPL-3.0 License' })).toBeVisible();
        await expect(page.getByText('Intel Simplified Software License')).toBeHidden();
        await expect(page.getByRole('button', { name: /^2 DINOv3/ })).toBeDisabled();

        const termsUrl =
            'https://www.ultralytics.com/license?utm_source=intel&utm_medium=referral&utm_campaign=geti-model-garden&utm_content=user-notice';
        const termsLink = page.getByRole('link', { name: termsUrl, exact: true });
        await expect(termsLink).toHaveAttribute('href', termsUrl);
        await expect(termsLink).toHaveAttribute('target', '_blank');

        await expect(page.getByRole('button', { name: 'Next' })).toBeDisabled();
        await page.getByRole('checkbox', { name: /I have read and agree to the Ultralytics/ }).check();
        await page.getByRole('button', { name: 'Next' }).click();

        await expect(page.getByText('2 of 2')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'DINOv3 License' })).toBeVisible();
        await expect(page.getByRole('checkbox')).toHaveCount(0);

        await page.getByRole('button', { name: 'Accept and continue' }).click();

        await expect(page.getByRole('heading', { name: 'License Agreements' })).toBeHidden();
        await expect(page).toHaveURL(/\/projects$/);
    });

    test('skips the license screen when it is already accepted', async ({ page, network }) => {
        network.use(
            http.get('/api/projects', ({ response }) => {
                return response(200).json([]);
            })
        );

        await page.goto('/');

        await expect(page.getByRole('heading', { name: 'License Agreements' })).toBeHidden();
        await expect(page).toHaveURL(/\/projects$/);
    });
});
