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
import { getMockDateScript } from '../../utils/time';
import {
    getMockedProjectAggregatesByTime,
    getMockedTimeAggregates,
    mockedCreditAccountsFew,
    mockedCreditAccountsMany,
    mockedMonthlyCreditConsumptionAggregation,
    mockedOrganizationBalance,
    mockedProjectNames,
} from './usage.mocks';

const organizationId = '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633';
test.describe('Usage page', () => {
    test.use({
        isSaaS: true,
        featureFlags: {
            FEATURE_FLAG_CREDIT_SYSTEM: true,
        },
    });

    test.beforeEach(async ({ registerApiResponse }) => {
        registerStoreSettings(registerApiResponse, {
            [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: {
                isEnabled: false,
            },
        });

        registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) => {
            return res(ctx.json(mockedOrganizationBalance));
        });
    });

    test('Current credit limit', async ({ page, registerApiResponse }) => {
        registerApiResponse('get_credit_accounts_api_v1_organizations__org_id__credit_accounts_get', (_, res, ctx) => {
            return res(ctx.json(mockedCreditAccountsFew));
        });

        await page.goto(paths.account.usage({ organizationId }));

        const renewableAmount = mockedCreditAccountsFew.credit_accounts.reduce(
            (acc, curr) => acc + curr.renewable_amount,
            0
        );

        await expect(page.getByTestId('credits-limit-card-available-credits-chart-label-text')).toHaveText(
            `${mockedOrganizationBalance.available}`
        );
        await expect(page.getByTestId('credits-limit-card-total-credits-chart-label-text')).toHaveText(
            `of ${mockedOrganizationBalance.incoming}`
        );
        await expect(page.getByTestId('credits-limit-card-renewable-credits-text')).toHaveText(
            `Monthly renewal of ${renewableAmount} credits`
        );
    });

    test('Credit accounts table with 2 elements', async ({ page, registerApiResponse }) => {
        registerApiResponse('get_credit_accounts_api_v1_organizations__org_id__credit_accounts_get', (_, res, ctx) => {
            return res(ctx.json(mockedCreditAccountsFew));
        });

        await page.goto(paths.account.usage({ organizationId }));

        // 1 header + 2 fixed rows
        await expect(page.getByTestId('credit-accounts-table-short').getByRole('row')).toHaveCount(3);
        await expect(page.getByRole('link', { name: 'Show all credit accounts' })).toBeHidden();
        await expect(page.getByTestId('credit-accounts-table-full')).toBeHidden();
    });

    test('Credit accounts table with 5 elements', async ({ page, registerApiResponse }) => {
        registerApiResponse('get_credit_accounts_api_v1_organizations__org_id__credit_accounts_get', (_, res, ctx) => {
            return res(ctx.json(mockedCreditAccountsMany));
        });

        await page.goto(paths.account.usage({ organizationId }));

        await expect(page.getByTestId('credit-accounts-table-short').getByRole('row')).toHaveCount(3);
        await expect(page.getByRole('link', { name: 'Show all credit accounts' })).toBeVisible();
        await expect(page.getByTestId('credit-accounts-table-full')).toBeHidden();
        await expect(page.getByTestId('credit-accounts-table-short').getByRole('row')).toHaveCount(3);

        await page.getByRole('link', { name: 'Show all credit accounts' }).click();

        await expect(page.getByTestId('credit-accounts-table-full')).toBeVisible();
        await expect(page.getByTestId('credit-accounts-table-full').getByRole('row')).toHaveCount(6);
    });

    test('Monthly credit consumption', async ({ registerApiResponse, page }) => {
        registerApiResponse(
            'get_credit_consumption_aggregates_api_v1_organizations__org_id__transactions_aggregates_get',
            (_, res, ctx) => {
                return res(ctx.json(mockedMonthlyCreditConsumptionAggregation));
            }
        );

        await page.goto(paths.account.usage({ organizationId }));

        await expect(page.getByTestId('monthly-credits-usage-card-credits-count')).toContainText('569');
        await expect(page.getByTestId('monthly-credits-usage-card-projects-count')).toContainText('2');
        await expect(page.getByTestId('monthly-credits-usage-card-images-count')).toContainText('207');
    });

    test('Projects consumption with month picker', async ({ page, registerApiResponse }) => {
        const fakeNow = new Date('2024-04-03').valueOf();
        await page.addInitScript(getMockDateScript(fakeNow));
        registerApiResponse(
            'get_credit_consumption_aggregates_api_v1_organizations__org_id__transactions_aggregates_get',
            (req, res, ctx) => {
                return res(ctx.json(getMockedProjectAggregatesByTime(req.query.from_date)));
            }
        );

        await page.goto(paths.account.usage({ organizationId }));

        await expect(page.getByTestId('projects-credit-consumption-month-picker-value-text')).toHaveText(
            'April / 2024'
        );
        await expect(page.getByLabel('Credit consumption by projects').getByText(/Undefined project/)).toHaveCount(1);
        await page.getByLabel('Select a month').nth(0).click();
        await page.getByText('Feb').click();
        await page.mouse.click(0, 0);
        await expect(page.getByTestId('projects-credit-consumption-month-picker-value-text')).toHaveText(
            'February / 2024'
        );
        await expect(page.getByLabel('Credit consumption by projects').getByText(/Undefined project/)).toHaveCount(5);
        await expect(page.getByRole('link', { name: 'Show all' })).toBeVisible();
        await page.getByRole('link', { name: 'Show all' }).click();
        await expect(page.getByLabel('Credit consumption by projects').getByText(/Undefined project/)).toHaveCount(7);
    });

    test('Consumption by time', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetAllProjectsNamesInAWorkspace', (_, res, ctx) => {
            return res(ctx.json(mockedProjectNames));
        });

        registerApiResponse(
            'get_credit_consumption_aggregates_api_v1_organizations__org_id__transactions_aggregates_get',
            (req, res, ctx) => {
                return res(ctx.json(getMockedTimeAggregates(req.query.project_id)));
            }
        );

        await page.goto(paths.account.usage({ organizationId }));

        await expect(page.getByLabel('Credit consumption by time').locator('path')).toHaveCount(4);

        await page.getByLabel(/select a project/i).click();
        await page.getByLabel(/show suggestions/i).click();
        await page.getByRole('option', { name: 'Project 1' }).click();
        await expect(page.getByLabel('Credit consumption by time').locator('path')).toHaveCount(1);

        await page.getByLabel('Clear project selection').click();
        await expect(page.getByLabel('Credit consumption by time').locator('path')).toHaveCount(4);
    });
});
