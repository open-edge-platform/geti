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
