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

import { annotatorTest as test } from '../.././../fixtures/annotator-test';

test.describe('Select all / unselect all annotations', () => {
    test.beforeEach(async ({ page, annotatorPath }) => {
        await page.goto(annotatorPath);

        await expect(page.getByRole('progressbar', { name: /loading/i })).toBeHidden();
    });

    test('Should select all annotations', async ({ annotationListPage, page }) => {
        const totalAnnotationsCount = await annotationListPage.getTotalAnnotations();
        expect(await annotationListPage.getTotalSelectedAnnotations()).toBe(0);

        await page.keyboard.press('Control+A');

        expect(totalAnnotationsCount).toBe(await annotationListPage.getTotalSelectedAnnotations());
    });

    test('Should unselect all selected annotations', async ({ annotationListPage, page }) => {
        const totalAnnotationsCount = await annotationListPage.getTotalAnnotations();
        expect(await annotationListPage.getTotalSelectedAnnotations()).toBe(0);

        await page.keyboard.press('Control+A');

        expect(totalAnnotationsCount).toBe(await annotationListPage.getTotalSelectedAnnotations());

        await page.keyboard.press('Control+D');

        expect(await annotationListPage.getTotalSelectedAnnotations()).toBe(0);
    });
});
