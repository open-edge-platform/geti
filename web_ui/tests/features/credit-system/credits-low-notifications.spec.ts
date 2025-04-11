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

import { expect } from '@playwright/test';

import { paths } from '../../../src/core/services/routes';
import { GLOBAL_MODALS_KEYS } from '../../../src/core/user-settings/dtos/user-settings.interface';
import { test } from '../../fixtures/base-test';
import { registerStoreSettings } from '../../utils/api';
import { getEmptyJobs, getScheduledTrainingCostJob } from './mocks';

const workspaceIdentifier = {
    workspaceId: '6101a',
    projectId: '6101b',
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
};

test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true }, isSaaS: true });

test.beforeEach(async ({ registerApiResponse }) => {
    registerStoreSettings(registerApiResponse, {
        [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: { isEnabled: true },
        [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: true },
        [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false },
    });
    registerApiResponse('GetJobs', (_, res, ctx) =>
        res(ctx.json(getScheduledTrainingCostJob([{ unit: 'image', amount: 5, consuming_date: '' }])))
    );
    registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
        res(ctx.json({ incoming: 100, available: 9 }))
    );
});

test.describe('Low and exhausted credits notifications', () => {
    test('Show low and exhausted credits notifications', async ({ page, registerApiResponse }) => {
        await page.goto(paths.project.index(workspaceIdentifier));

        await expect(page.getByText(/Credits are low/i)).toBeVisible({ timeout: 5000 });
        await page.getByText(/Close/i).click();

        registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
            res(ctx.json({ incoming: 100, available: 0 }))
        );
        // Update jobs response to trigger balance query invalidation
        registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getEmptyJobs())));

        await expect(page.getByText(/Credits have been exhausted/i)).toBeVisible({ timeout: 5000 });
    });

    test('Show exhausted credits notifications', async ({ page, registerApiResponse }) => {
        registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
            res(ctx.json({ incoming: 100, available: 0 }))
        );

        await page.goto(paths.project.index(workspaceIdentifier));
        await expect(page.getByText(/Credits have been exhausted/i)).toBeVisible({ timeout: 5000 });
    });
});
