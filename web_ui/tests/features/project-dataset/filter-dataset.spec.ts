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

import { expect } from '@playwright/test';

import { test } from '../../fixtures/base-test';
import {
    acceptFilter,
    checkChipsValue,
    checkMediaNameFilter,
    checkSearchByNameFilterChip,
    closeSearchByNameFilterPopover,
    openAndTypeIntoSearchField,
    triggerFilterModal,
} from '../../fixtures/search-by-name';
import { projects } from './mocks';

const [project] = projects.projects;
// eslint-disable-next-line max-len
const url = `organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/${project.id}}`;

test.describe('filter dataset', () => {
    test.beforeEach(async ({ registerApiResponse }) => {
        registerApiResponse('GetAllProjectsInAWorkspace', (_, res, ctx) => res(ctx.json(projects)));
    });

    test('"Media search" filter is listed in "Media Filter" after reloading', async ({ page }) => {
        const nameToSearch = 'This is a name test';
        await page.goto('/', { timeout: 15000 });
        await page.locator(`#project-id-${project.id}`).click();
        await expect(page.getByLabel('open dataset menu')).toBeVisible();

        const mediaSearchButton = page.locator('role=button[name="Search media by name (regex allowed)"]');
        await mediaSearchButton.click();
        const mediaSearch = page.getByLabel('media search');
        await mediaSearch.fill(nameToSearch);
        await mediaSearch.press('Enter');

        await page.reload();

        await page.locator('role=button[name="Filter media"]').click();
        await expect(page.locator('#filter-dialog-title')).toBeVisible();

        const filterInput = page.getByLabel('media-filter-name');
        await expect(filterInput).toHaveValue(nameToSearch);
    });

    test('Check if typing filter will set chip with the filter and after removing it filter is removed', async ({
        page,
    }) => {
        /** Implementation of test cases:
         * test_annotator_dataset_searchbar_auto_label[media page]
         * test_annotator_dataset_searchbar_remove_label[media page]
         */

        await page.goto(url, { timeout: 15000 });
        await expect(page.getByLabel('open dataset menu')).toBeVisible();

        await openAndTypeIntoSearchField(page, 'cat');

        await closeSearchByNameFilterPopover(page);

        await expect(page.getByTestId('chip-search-rule-id')).toHaveText('Media name contains cat');

        await page.getByRole('button', { name: 'remove-rule-search-rule-id' }).click();

        await triggerFilterModal(page);
        expect(await page.locator('#media-filter-delete-row').count()).toBe(0);
    });

    test('Check if submitting filter shorter than 3 chars will add chip with filter', async ({ page }) => {
        /** test_annotator_dataset_searchbar_manual_label[media page] */
        await page.goto('/', { timeout: 15000 });
        await page.locator(`#project-id-${project.id}`).click();
        await expect(page.getByLabel('open dataset menu')).toBeVisible();

        await openAndTypeIntoSearchField(page, 'im');
        await acceptFilter(page);

        await checkChipsValue(page, 'Media name contains im');
    });

    test('Check if changing search will update filter rule', async ({ page }) => {
        /** test_annotator_dataset_searchbar_overwrite_label[media page] */

        await page.goto('/', { timeout: 15000 });
        await page.locator(`#project-id-${project.id}`).click();
        await expect(page.getByLabel('open dataset menu')).toBeVisible();

        await checkSearchByNameFilterChip(page, 'cat');

        await checkSearchByNameFilterChip(page, 'dog');
        await triggerFilterModal(page);

        await checkMediaNameFilter(page, 'dog');
    });
});
