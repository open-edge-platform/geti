// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { expect, Page } from '@playwright/test';

import { GLOBAL_MODALS_KEYS } from '../../../src/core/user-settings/dtos/user-settings.interface';
import { test } from '../../fixtures/base-test';
import { productsPolicy } from '../../mocks/credit-system/mocks';
import { registerStoreSettings } from '../../utils/api';

const organizationId = '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633';
const workspaceId = '61011e42d891c82e13ec92da';
const HOME_URL = paths.home({ workspaceId, organizationId });
const ACCOUNT_URL = paths.account.index({ organizationId });

const waitForProgressBarToBeRemoved = async (page: Page) => {
    await expect(page.getByRole('progressbar')).toBeHidden();
};

test.use({ isSaaS: true });
test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true } });

test.describe('welcome modal', () => {
    test.beforeEach(async ({ registerApiResponse }) => {
        registerStoreSettings(registerApiResponse);
        registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
            res(ctx.json({ incoming: 10, available: 100 }))
        );
        registerApiResponse('get_all_products_api_v1_products_get', (_, res, ctx) => res(ctx.json(productsPolicy)));
    });

    test('stays hidden after being closed by the user', async ({ page, registerFeatureFlags }) => {
        registerFeatureFlags({ FEATURE_FLAG_CREDIT_SYSTEM: true });
        await page.goto(HOME_URL);

        await expect(page.getByRole('progressbar')).toBeHidden();
        await page.getByRole('button', { name: /Start exploring now/i }).click();

        await page.reload();

        await waitForProgressBarToBeRemoved(page);
        await expect(page.getByRole('button', { name: /Start exploring now/i })).toBeHidden();
    });
});

test.describe('exhausted modal', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerStoreSettings(registerApiResponse, { [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false } });
        registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
            res(ctx.json({ incoming: 10, available: 0 }))
        );
    });

    const modalHeadSelector = (page: Page) => {
        return page.getByText(/credits have been exhausted/i, { exact: false });
    };

    test('it is visible in multiple pages', async ({ page }) => {
        await page.goto(HOME_URL);

        await waitForProgressBarToBeRemoved(page);
        await expect(await modalHeadSelector(page)).toBeVisible();
    });

    test('stays hidden after being closed by the user', async ({ page }) => {
        await page.goto(HOME_URL);

        await waitForProgressBarToBeRemoved(page);
        await expect(await modalHeadSelector(page)).toBeVisible();

        await page.getByRole('button', { name: /close/i }).click();

        await page.goto(ACCOUNT_URL);
        await waitForProgressBarToBeRemoved(page);

        await expect(page.getByText(/credits have been exhausted/i)).toBeHidden();
    });
});

test.describe('flag is Off', () => {
    test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: false } });

    test('welcome modal is hidden', async ({ page }) => {
        await page.goto(HOME_URL);

        await waitForProgressBarToBeRemoved(page);
        await expect(page.getByRole('button', { name: /Start exploring now/i })).toBeHidden();
    });

    test('exhausted nodal is hidden', async ({ page, registerApiResponse }) => {
        registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
            res(ctx.json({ incoming: 10, available: 0 }))
        );

        await page.goto(HOME_URL);

        await waitForProgressBarToBeRemoved(page);
        await expect(page.getByText(/credits have been exhausted/i, { exact: false })).toBeHidden();
    });
});
