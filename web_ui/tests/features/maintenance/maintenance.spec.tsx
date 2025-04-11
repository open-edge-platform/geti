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

import { GENERAL_SETTINGS_KEYS } from '../../../src/core/user-settings/dtos/user-settings.interface';
import { expect, test } from '../../fixtures/base-test';
import { settings } from '../../fixtures/open-api/mocks';
import { switchCallsAfter } from '../../utils/api';

test.use({
    isSaaS: true,
    featureFlags: {
        FEATURE_FLAG_MAINTENANCE_BANNER: true,
    },
});

// https://www.epochconverter.com/
const mockStartDate = 1711312113376; // April 28, 03:56
const mockEndDate = 1711513116880; // September 10, 14:14

test.describe('Maintenance', () => {
    test.beforeEach(async ({ page, baseURL }) => {
        await page.route(`${baseURL}/config.geti.example.com`, async (route) => {
            await route.fulfill({
                status: 200,
                body: JSON.stringify({
                    maintenance: {
                        enabled: true,
                        window: {
                            start: mockStartDate,
                            end: mockEndDate,
                        },
                    },
                }),
            });
        });
    });

    test('Maintenance banner displays correct information', async ({ page }) => {
        await page.goto('/');

        await expect(page.getByText(/Scheduled maintenance/)).toBeVisible();
        await expect(page.getByText(/28 of April, 03:56/)).toBeVisible();
        await expect(page.getByText(/10 of September, 14:14/)).toBeVisible();
    });

    test('Maintenance banner dismissal/retrieval', async ({ page, registerApiResponse }) => {
        const switchAfter = switchCallsAfter(1);
        registerApiResponse(
            'GetSettings',
            switchAfter([
                async (_, res, ctx) => {
                    return res(ctx.status(200), ctx.json({ settings }));
                },
                async (_, res, ctx) => {
                    return res(
                        ctx.status(200),
                        ctx.json({
                            settings: JSON.stringify({
                                ...JSON.parse(settings),
                                [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: {
                                    wasDismissed: true,
                                    window: {
                                        start: mockStartDate,
                                        end: mockEndDate,
                                    },
                                },
                            }),
                        })
                    );
                },
            ])
        );

        await page.goto('/');

        // check that the banner is displayed
        await expect(page.getByText(/Scheduled maintenance/)).toBeVisible();
        await expect(page.getByText(/28 of April, 03:56/)).toBeVisible();
        await expect(page.getByText(/10 of September, 14:14/)).toBeVisible();

        // dismiss the banner
        await page.getByRole('button', { name: 'dismiss banner' }).click();
        await expect(page.getByText(/Scheduled maintenance/)).toBeHidden();

        // refresh page
        await page.reload();

        // check that the banner is not present
        await expect(page.getByText(/Scheduled maintenance/)).toBeHidden();
    });
});
