// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, http, test } from '../fixtures';

test.describe('License agreement (Tauri)', () => {
    test('shows the license screen and accepts the license on Windows', async ({ page, network }) => {
        let licenseAccepted = false;

        network.use(
            http.get('/api/system/info', ({ response }) => {
                return response(200).json({
                    license_accepted: licenseAccepted,
                    platform: 'windows',
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

        await test.step('license screen is shown when license is not accepted', async () => {
            await page.goto('/');

            await expect(page.getByRole('heading', { name: /License Agreement/i })).toBeVisible();
            await expect(page.getByRole('link', { name: /Intel Simplified Software License/i })).toBeVisible();
            await expect(page.getByRole('link', { name: /DINOv3 License/i })).toBeVisible();
        });

        await test.step('accepting the license redirects to the projects page', async () => {
            await page.getByRole('button', { name: /Accept and continue/i }).click();

            await expect(page.getByRole('heading', { name: /License Agreement/i })).toBeHidden();
            await expect(page).toHaveURL(/\/projects$/);
        });
    });

    test('skips the license screen on non-Windows platforms', async ({ page, network }) => {
        network.use(
            http.get('/api/system/info', ({ response }) => {
                return response(200).json({
                    license_accepted: false,
                    platform: 'linux',
                });
            }),
            http.get('/api/projects', ({ response }) => {
                return response(200).json([]);
            })
        );

        await page.goto('/');

        await expect(page.getByRole('heading', { name: /License Agreement/i })).toBeHidden();
    });

    test('skips the license screen when it is already accepted on Windows', async ({ page, network }) => {
        network.use(
            http.get('/api/system/info', ({ response }) => {
                return response(200).json({
                    license_accepted: true,
                    platform: 'windows',
                });
            }),
            http.get('/api/projects', ({ response }) => {
                return response(200).json([]);
            })
        );

        await page.goto('/');

        await expect(page.getByRole('heading', { name: /License Agreement/i })).toBeHidden();
    });

    test('shows error state when system info is unavailable', async ({ page, network }) => {
        network.use(
            http.get('/api/system/info', ({ response }) => {
                // @ts-expect-error Simulate server error
                return response(500).json({});
            })
        );

        await page.goto('/');

        await expect(page.getByRole('heading', { name: 'Server Error' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Refresh' })).toBeVisible();
    });
});
