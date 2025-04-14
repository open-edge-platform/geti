// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { test } from '../../../fixtures/base-test';
import { annotatorUrl, project } from '../../../mocks/segmentation/mocks';
import { VIEWPORT_TYPE } from '../../../utils/test-type';

const expectOverlayBeVisible = async (page: Page, name: string) => {
    const annotationListButton = page.getByLabel(name);
    await expect(annotationListButton).toBeVisible();
    await annotationListButton.click();

    await expect(page.getByTestId(`${name} overlay`)).toBeVisible();
    // click outside
    await page.getByLabel(/^Selection$/).click();

    await expect(page.getByTestId(`${name} overlay`)).toBeHidden();
};

test.describe('sidebar', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json({})));
    });

    test('collapse/open sidebar', async ({ page }) => {
        await page.goto(annotatorUrl);

        const toggleButton = page.getByLabel('toggle sidebar');
        await expect(page.getByTestId('sidebar-split-panel')).toBeVisible();
        await expect(page.getByTestId('sidebar-panel')).toBeHidden();

        await toggleButton.click();
        await expect(page.getByTestId('sidebar-panel')).toBeVisible();
        await expect(page.getByTestId('sidebar-split-panel')).toBeHidden();
    });

    test(`${VIEWPORT_TYPE.MOBILE} collapse sidebar`, async ({ page }) => {
        await page.goto(annotatorUrl);

        await expect(page.getByTestId('sidebar-panel')).toBeVisible();
        await expect(page.getByTestId('toggle sidebar')).toBeHidden();
        await expect(page.getByTestId('sidebar-split-panel')).toBeHidden();

        await expectOverlayBeVisible(page, 'annotation list');
        await expectOverlayBeVisible(page, 'dataset accordion');
    });
});
