// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, test } from '../../fixtures/base-test';
import { ACCOUNT_URL } from './mocks';

test.describe('Account page - analytics tab', () => {
    const accountAnalyticsUrl = ACCOUNT_URL('5b1f89f3-aba5-4a5f-84ab-de9abb8e0633', 'analytics');
    const tabs = ['metrics', 'traces', 'logs'];

    test.beforeEach(async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProductInfo', (_, res, ctx) => {
            return res(
                ctx.json({
                    'product-version': '2.9.0',
                    'build-version': '2.9.0-test-20250428191218',
                    'smtp-defined': 'True',
                    'intel-email': 'Geti.Team@intel.com',
                    grafana_enabled: true,
                    environment: 'on-prem',
                    'gpu-provider': 'intel',
                })
            );
        });
        await page.goto(accountAnalyticsUrl);
    });

    test('Check tab elements', async ({ page }) => {
        const analyticsCard = page.getByTestId('analytics-card');
        await expect(analyticsCard).toBeVisible();

        await expect(analyticsCard.getByRole('heading', { name: 'Analytics' })).toBeVisible();
        await expect(
            analyticsCard.getByText(
                'Operational dashboards for your data. Understand your data, ' +
                    'gain deeper insights, and make better data-driven decisions.'
            )
        ).toBeVisible();

        await expect(analyticsCard.getByRole('button', { name: 'Go to Analytics' })).toBeVisible();

        await expect(page.getByTestId('downloadable-item-metrics')).toBeVisible();
        await expect(page.getByTestId('downloadable-item-traces')).toBeVisible();
        await expect(page.getByTestId('downloadable-item-logs')).toBeVisible();
    });

    for (const tab of tabs) {
        test(`Check ${tab} download`, async ({ page }) => {
            const isNotTracesTab = tab !== 'traces';

            await page
                .getByTestId(`downloadable-item-${tab}`)
                .getByRole('button', { name: `Download ${tab}` })
                .click();

            const modal = page.getByTestId('modal');
            await expect(modal.getByText(`Export ${tab}`)).toBeVisible();
            await expect(modal.locator(`#dates-range-${tab}-id`)).toBeVisible();

            if (isNotTracesTab) {
                await expect(modal.getByRole('radiogroup')).toBeVisible();

                await expect(modal.getByRole('button', { name: 'Close' })).toBeEnabled();
                await expect(modal.getByRole('button', { name: 'Export' })).toBeDisabled();

                await modal.getByRole('radio', { name: 'Application' }).click();
                await expect(modal.getByRole('button', { name: 'Export' })).toBeEnabled();
                await modal.getByRole('radio', { name: 'Server' }).click();
                await expect(modal.getByRole('button', { name: 'Export' })).toBeEnabled();
            } else {
                await expect(modal.getByRole('button', { name: 'Close' })).toBeEnabled();
                await expect(modal.getByRole('button', { name: 'Export' })).toBeEnabled();
            }

            await modal.getByRole('button', { name: 'Export' }).click();
            await page.waitForURL(`**/api/v1/logs?type=${isNotTracesTab ? 'k8s_' : ''}${tab}**`);
        });
    }
});
