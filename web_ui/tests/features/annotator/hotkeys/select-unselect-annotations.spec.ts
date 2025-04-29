// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
