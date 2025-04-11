// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
