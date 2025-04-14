// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { test } from '../../../fixtures/base-test';
import { waitForLoadingToBeFinished } from '../../../utils/assertions';
import {
    annotatorUrl,
    media,
    project,
    userAnnotationsResponse,
    userFewAnnotationsResponse,
} from './../../../mocks/segmentation/mocks';

const getAnnotation = async (page: Page, annotationName: string) => page.locator(`#annotation-${annotationName}`);
const toggleAnnotation = async (page: Page) => {
    await page.getByTestId('annotation-all-annotations-toggle-visibility').click();
};

test.describe('Annotator actions', () => {
    test.beforeEach(({ registerApiResponse }) => {
        // Important to project test
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
    });

    test('Hide show annotations - one annotation', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json({ ...userAnnotationsResponse })));

        await page.goto(annotatorUrl);
        await waitForLoadingToBeFinished(page);

        await toggleAnnotation(page);
        await expect(await getAnnotation(page, 'horse')).toBeHidden();

        await toggleAnnotation(page);
        await expect(await getAnnotation(page, 'horse')).toBeVisible();
    });

    test('Hide show annotations - many annotations', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json({ ...userFewAnnotationsResponse })));

        await page.goto(annotatorUrl);
        await waitForLoadingToBeFinished(page);

        await toggleAnnotation(page);
        await expect(await getAnnotation(page, 'saddled')).toBeHidden();
        await expect(await getAnnotation(page, 'horse')).toBeHidden();

        await toggleAnnotation(page);
        await expect(await getAnnotation(page, 'saddled')).toBeVisible();
        await expect(await getAnnotation(page, 'horse')).toBeVisible();
    });
});
