// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, http, test } from '../fixtures';

test.describe('License agreement (web)', () => {
    test('never shows the license screen, even when the backend reports it is unaccepted', async ({
        page,
        network,
    }) => {
        network.use(
            http.get('/api/system/info', ({ response }) => {
                return response(200).json({
                    license_accepted: false,
                    platform: 'windows',
                });
            }),
            http.get('/api/projects', ({ response }) => {
                return response(200).json([]);
            })
        );

        await page.goto('/');

        await expect(page.getByRole('heading', { name: /License Agreement/i })).toBeHidden();
        await expect(page).toHaveURL(/\/projects$/);
    });
});
