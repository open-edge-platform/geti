// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { getMockedOrganizationDTO } from '../../../src/test-utils/mocked-items-factory/mocked-organization';
import { test } from '../../fixtures/base-test';
import { mockedCreditAccounts, mockedOrganizationsResponse } from './mocks';

const organizationId = 'organization-id';
const organizationName = 'Test org';

test.describe('Intel admin credit accounts', () => {
    test.use({ isSaaS: true, featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true } });

    test.beforeEach(async ({ registerApiResponse }) => {
        const creditAccounts = mockedCreditAccounts;

        registerApiResponse('Organization_find', (_, res, ctx) =>
            res(
                ctx.json({
                    ...mockedOrganizationsResponse,
                    organizations: [
                        getMockedOrganizationDTO({
                            id: organizationId,
                            name: organizationName,
                        }),
                    ],
                })
            )
        );

        registerApiResponse('get_credit_accounts_api_v1_organizations__org_id__credit_accounts_get', (_, res, ctx) =>
            // @ts-expect-error Issue in OpenApi types
            res(ctx.json(mockedCreditAccounts))
        );

        registerApiResponse(
            'create_credit_account_api_v1_organizations__org_id__credit_accounts_post',
            (req, res, ctx) => {
                creditAccounts.total_matched += 1;
                creditAccounts.credit_accounts.push({
                    id: `${Math.floor(Math.random() * 100) + 3}`,
                    organization_id: organizationId,
                    created: new Date().valueOf(),
                    updated: new Date().valueOf(),
                    name: req.body.name,
                    balance: {
                        incoming: req.body.init_amount,
                        available: req.body.init_amount,
                        blocked: 0,
                    },
                    renewable_amount: req.body.renewable_amount ?? null,
                    renewal_day_of_month: req.body.renewal_day_of_month ?? null,
                    expires: req.body.expires ?? null,
                });

                return res(ctx.status(201));
            }
        );

        registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
            res(ctx.json({ incoming: 600, available: 200 }))
        );

        registerApiResponse(
            'edit_account_balance_api_v1_organizations__org_id__credit_accounts__account_id__balance_put',
            (req, res, ctx) => {
                const creditAccountId = creditAccounts.credit_accounts.findIndex(
                    (account) => account.id === req.params.account_id
                );

                if (creditAccountId !== -1) {
                    creditAccounts.credit_accounts[creditAccountId].balance.available +=
                        (req.body.add || 0) - (req.body.subtract || 0);

                    // @ts-expect-error Issue in OpenApi types
                    return res(ctx.json(creditAccounts.credit_accounts[creditAccountId]));
                } else {
                    return res(ctx.status(404));
                }
            }
        );
        registerApiResponse(
            'update_credit_account_api_v1_organizations__org_id__credit_accounts__acc_id__put',
            (req, res, ctx) => {
                const creditAccountId = creditAccounts.credit_accounts.findIndex(
                    (account) => account.id === req.params.acc_id
                );

                if (creditAccountId !== -1) {
                    creditAccounts.credit_accounts[creditAccountId] = {
                        ...creditAccounts.credit_accounts[creditAccountId],
                        ...req.body,
                    };

                    // @ts-expect-error Issue in OpenApi types
                    return res(ctx.json(creditAccounts.credit_accounts[creditAccountId]));
                } else {
                    return res(ctx.status(404));
                }
            }
        );
    });

    test('Credit accounts CRUD', async ({ page, intelAdminPage }) => {
        await intelAdminPage.goToOrganizationsListPage();
        await page.getByRole('row', { name: organizationName }).click();
        await page.getByText('Credits').click();
        await expect(page.getByRole('heading', { name: /credit accounts/i })).toBeVisible();
        await expect(page.getByTestId('organization-balance-value')).toHaveText('200');
        await expect(page.getByRole('rowgroup').nth(1).locator('role=row')).toHaveCount(2);

        // Create credit account
        await page.getByRole('button', { name: 'Add credits' }).click();
        await page.getByLabel('Amount').fill('200');
        await page.getByRole('button', { name: 'Save' }).click();
        await expect(page.getByRole('dialog')).toBeVisible();
        await page.getByLabel('Name').fill('Test Credit Account');
        await page.getByRole('button', { name: 'Save' }).click();
        await expect(page.getByRole('dialog')).toBeHidden();
        await expect(page.getByRole('rowgroup').nth(1).locator('role=row')).toHaveCount(3);

        // Edit balance
        await page.getByRole('row', { name: 'Test Credit Account' }).getByRole('gridcell').nth(5).click();
        await page.getByText('Edit balance').click();
        await page.getByRole('radio', { name: 'Subtract' }).click();
        await page.getByLabel('Balance', { exact: true }).fill('100');
        // It's needed to focus out input field
        await page.getByRole('dialog').click();
        await page.getByRole('button', { name: 'Save' }).click();
        await expect(page.getByRole('row', { name: 'Test Credit Account' }).getByRole('gridcell').first()).toHaveText(
            '100'
        );

        // Edit credit account
        await page.getByRole('row', { name: 'Test Credit Account' }).getByRole('gridcell').nth(5).click();
        await page.getByText('Edit credit account').click();
        await page.getByLabel('Name').fill('Test Credit Account new');
        await page.getByRole('dialog').click();
        await page.getByRole('button', { name: 'Save' }).click();
        await expect(page.getByRole('row', { name: 'Test Credit Account new' })).toBeVisible();
    });
});
