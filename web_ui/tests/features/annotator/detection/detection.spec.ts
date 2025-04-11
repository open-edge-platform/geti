// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect } from '@playwright/test';
import isEmpty from 'lodash/isEmpty';

import { DOMAIN } from '../../../../src/core/projects/core.interface';
import { checkCommonElements, checkDetectionTools, checkNumberOfTools } from '../../../fixtures/annotator-test';
import { test } from '../../../fixtures/base-test';
import { getImagesNumber } from '../../../fixtures/images';
import {
    acceptFilter,
    checkChipsValue,
    checkMediaNameFilter,
    checkSearchByNameFilterChip,
    closeSearchByNameFilterPopover,
    openAndTypeIntoSearchField,
    triggerFilterModal,
} from '../../../fixtures/search-by-name';
import { waitForLoadingToBeFinished } from '../../../utils/assertions';
import { allImages, annotatorUrl, filteredImages, media, project } from './../../../mocks/detection/mocks';

test.describe('Detection', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
        registerApiResponse('FilterMedia', (req, res, ctx) => {
            if (isEmpty(req.requestBody)) {
                return res(ctx.json(allImages));
            } else {
                return res(ctx.json(filteredImages));
            }
        });
    });

    test('Annotator page elements', async ({ page }) => {
        await page.goto(annotatorUrl, { timeout: 15000 });
        await waitForLoadingToBeFinished(page);
        await expect(page.getByTestId('project-name-domain-id')).toHaveText('Example detection project@ Detection');

        await checkNumberOfTools(page, 3);

        await checkDetectionTools(page);

        await checkCommonElements(page, DOMAIN.DETECTION);
    });

    test('Check if typing less than 3 chars calls search after pressing Enter', async ({ page }) => {
        /** test_annotator_dataset_searchbar_less_than_3_chars */
        await page.goto(annotatorUrl, { timeout: 15000 });
        await waitForLoadingToBeFinished(page);

        await openAndTypeIntoSearchField(page, 'im');
        const numberOfImages = await getImagesNumber(page);

        expect(numberOfImages).toBe(3);

        await acceptFilter(page);

        expect(await getImagesNumber(page)).toBe(1);
    });

    test('Check if typing at least 3 chars calls search', async ({ page }) => {
        /** test_annotator_dataset_searchbar_at_least_3_chars */
        await page.goto(annotatorUrl, { timeout: 15000 });
        await waitForLoadingToBeFinished(page);

        await expect(async () => {
            expect(await getImagesNumber(page)).toBe(3);
        }).toPass();

        await openAndTypeIntoSearchField(page, 'image');
        await waitForLoadingToBeFinished(page);

        await expect(async () => {
            expect(await getImagesNumber(page)).toBe(1);
        }).toPass();
    });

    test('Check if typing filter will set chip with the filter and after removing it filter is removed', async ({
        page,
    }) => {
        /** Implementation of test cases:
         * test_annotator_dataset_searchbar_auto_label[annotatorPage]
         * test_annotator_dataset_searchbar_remove_label[annotatorPage]
         */
        await page.goto(annotatorUrl, { timeout: 15000 });
        await waitForLoadingToBeFinished(page);

        await openAndTypeIntoSearchField(page, 'cat');

        // Close search popout
        await closeSearchByNameFilterPopover(page);
        // Dismiss tooltip covering close button on filter chip
        await page.mouse.move(0, 0);
        await expect(page.getByTestId('chip-search-rule-id')).toHaveText('Media name contains cat');

        await page.getByRole('button', { name: 'remove-rule-search-rule-id' }).click();
        await expect(page.getByTestId('chip-search-rule-id')).toBeHidden();

        await triggerFilterModal(page);
        expect(await page.locator('#media-filter-delete-row').count()).toBe(0);
        await page.keyboard.press('Escape');

        expect(await getImagesNumber(page)).toBe(3);
    });

    test('Check if submitting filter shorter than 3 chars will add chip with filter', async ({ page }) => {
        /** test_annotator_dataset_searchbar_manual_label[annotatorPage] */
        await page.goto(annotatorUrl, { timeout: 15000 });
        await waitForLoadingToBeFinished(page);

        await openAndTypeIntoSearchField(page, 'im');
        await acceptFilter(page);

        await page.mouse.click(0, 0);

        await checkChipsValue(page, 'Media name contains im');
    });

    test('Check if changing search will update filter rule', async ({ page }) => {
        /** test_annotator_dataset_searchbar_overwrite_label[annotatorPage] */
        await page.goto(annotatorUrl, { timeout: 15000 });
        await waitForLoadingToBeFinished(page);

        await checkSearchByNameFilterChip(page, 'cat');

        await checkSearchByNameFilterChip(page, 'dog');

        await triggerFilterModal(page);

        await checkMediaNameFilter(page, 'dog');
    });

    test('Check if searching in active set will apply filter and switch to dataset - less than 3 chars', async ({
        page,
    }) => {
        /** test_annotator_dataset_searchbar_active_set_checkout[less than 3 chars] */
        await page.goto(annotatorUrl, { timeout: 15000 });
        await waitForLoadingToBeFinished(page);

        await page.getByTestId('selected-annotation-dataset-id').click();
        await page.getByRole('option', { name: 'Active set' }).click();

        await openAndTypeIntoSearchField(page, 'im');

        await expect(page.getByTestId('selected-annotation-dataset-id')).toHaveText('Active set');

        await acceptFilter(page);
        await expect(page.getByTestId('selected-annotation-dataset-id')).toHaveText('Dataset');

        expect(await getImagesNumber(page)).toBe(1);
    });

    test('Check if searching in active set will apply filter and switch to dataset - 3 chars', async ({ page }) => {
        /** test_annotator_dataset_searchbar_active_set_checkout[exact 3 chars] */
        await page.goto(annotatorUrl, { timeout: 15000 });
        await waitForLoadingToBeFinished(page);

        await page.getByTestId('selected-annotation-dataset-id').click();
        await page.getByRole('option', { name: 'Active set' }).click();

        await openAndTypeIntoSearchField(page, 'cat');

        await expect(page.getByTestId('selected-annotation-dataset-id')).toHaveText('Dataset');

        expect(await getImagesNumber(page)).toBe(1);
    });

    test('Check if searching in dataset using name with space is working', async ({ page }) => {
        await page.goto(annotatorUrl, { timeout: 15000 });

        await waitForLoadingToBeFinished(page);

        await openAndTypeIntoSearchField(page, 'this is dog ');
        await checkSearchByNameFilterChip(page, 'this is dog');

        await openAndTypeIntoSearchField(page, 'file');
        await checkSearchByNameFilterChip(page, 'this is dog file');
    });
});
