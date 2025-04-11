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

import * as path from 'path';

import { expect } from '@playwright/test';

import { AnnotationDTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { registerFullImage } from '../../../utils/api';
import {
    annotationResponse,
    annotatorUrl,
    project,
    segmentationPredictionsResponse,
    segmentationProject,
    segmentationUrl,
    urlWithFilter,
} from './mocks';

test.beforeEach(({ registerApiResponse }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
    registerFullImage(registerApiResponse, path.resolve(__dirname, './many-cards.jpeg'));

    registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(annotationResponse)));
});

test('Setting annotations filter', async ({ page, annotationListPage }) => {
    await page.goto(annotatorUrl);

    await page.getByRole('button', { name: /filter annotations/i }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    await page
        .getByRole('button', {
            name: /click to show child labels/i,
        })
        .click();

    await page
        .getByRole('listitem', { name: /spades/i })
        .getByRole('checkbox')
        .click();

    await page.getByRole('listitem', { name: /8/i }).getByRole('checkbox').click();

    // Dismiss dialog
    await page.mouse.click(0, 0);
    await expect(dialog).toBeHidden();

    await annotationListPage.expectTotalAnnotationsToBe(4);
});

test('Annotations with pre defined filter from url', async ({ page, annotationListPage }) => {
    await page.goto(urlWithFilter);

    await expect(page.getByRole('button', { name: /filter annotations/i })).toBeVisible();
    await page.getByRole('button', { name: /refresh filter/i }).click();

    // Check that the annotations have been filtered
    await annotationListPage.expectTotalAnnotationsToBe(4);

    await page
        .getByLabel(/Filter Spades/i)
        .getByRole('button')
        .click();
    await annotationListPage.expectTotalAnnotationsToBe(2);

    await page
        .getByLabel(/Filter 8/i)
        .getByRole('button')
        .click();

    await annotationListPage.expectTotalAnnotationsToBe(12);
});

test('Refreshing filters', async ({ page, boundingBoxTool, annotationListPage }) => {
    await page.goto(urlWithFilter);

    await expect(page.getByRole('button', { name: /filter annotations/i })).toBeVisible();
    await page.getByRole('button', { name: /refresh filter/i }).click();

    await annotationListPage.expectTotalAnnotationsToBe(4);

    await expect(page.getByRole('button', { name: /refresh filter/i })).toBeHidden();

    await boundingBoxTool.drawBoundingBox({ x: 10, y: 10, width: 100, height: 100 });
    await annotationListPage.expectTotalAnnotationsToBe(5);
    await expect(page.getByRole('button', { name: /refresh filter/i })).toBeVisible();
});

test('Clearing filters before submitting annotations', async ({
    page,
    boundingBoxTool,
    annotationListPage,
    registerApiResponse,
}) => {
    let storedAnnotations: AnnotationDTO[] = [];
    registerApiResponse('CreateImageAnnotation', (req, res, ctx) => {
        storedAnnotations = req.body.annotations as AnnotationDTO[];

        return res(ctx.status(200));
    });

    await page.goto(urlWithFilter);

    // Create a new annotation that is excluded from the filter
    await boundingBoxTool.selectTool();
    await boundingBoxTool.drawBoundingBox({ x: 10, y: 10, width: 100, height: 100 });

    await page.getByRole('button', { name: /refresh filter/i }).click();
    await annotationListPage.expectTotalAnnotationsToBe(4);

    await page.getByRole('button', { name: /Submit/i }).click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await page.getByRole('button', { name: 'Clear filter' }).click();
    await expect(dialog).toBeHidden();

    // Check that the filter has been removed
    await annotationListPage.expectTotalAnnotationsToBe(13);

    // Check that we can now submit annotations without the dialog
    await page.getByRole('button', { name: /Submit/i }).click();
    expect(storedAnnotations).toHaveLength(13);
});

test('Submitting annotations without clearing filter', async ({
    page,
    boundingBoxTool,
    registerApiResponse,
    annotationListPage,
}) => {
    let storedAnnotations: AnnotationDTO[] = [];
    registerApiResponse('CreateImageAnnotation', (req, res, ctx) => {
        storedAnnotations = req.body.annotations as AnnotationDTO[];

        return res(ctx.status(200));
    });

    await page.goto(urlWithFilter);

    // Create a new annotation that is excluded from the filter
    await boundingBoxTool.selectTool();
    await boundingBoxTool.drawBoundingBox({ x: 10, y: 10, width: 100, height: 100 });

    // Refresh the filter so that it is applied to the new annotaiton
    await page.getByRole('button', { name: /refresh filter/i }).click();
    await annotationListPage.expectTotalAnnotationsToBe(4);
    await annotationListPage.expectTotalAnnotationsToBe(4);

    await page.getByRole('button', { name: /Submit/i }).click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await page.getByRole('button', { name: 'Submit anyway' }).click();
    await expect(dialog).toBeHidden();

    // Check that all annotations were submitted
    expect(storedAnnotations).toHaveLength(13);
});

test('Clearing the filter', async ({ page, annotationListPage }) => {
    await page.goto(urlWithFilter);

    await page.getByRole('button', { name: /filter annotations/i }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    await page
        .getByRole('button', {
            name: /clear all/i,
        })
        .click();

    // Dismiss dialog
    await page.mouse.click(0, 0);
    await expect(dialog).toBeHidden();

    await annotationListPage.expectTotalAnnotationsToBe(12);
});

test.describe('threshold', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(segmentationProject)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...annotationResponse, annotations: [] }))
        );
        registerApiResponse('GetSinglePrediction', (_, res, ctx) =>
            res(ctx.json({ predictions: segmentationPredictionsResponse.annotations }))
        );
    });

    test('filter all element under threshold "90"', async ({ page, annotationListPage }) => {
        await page.goto(segmentationUrl);

        await annotationListPage.expectTotalAnnotationsToBe(segmentationPredictionsResponse.annotations.length);

        await annotationListPage.moveThresholdSliderUp(90);

        await annotationListPage.expectTotalAnnotationsToBe(0);
    });

    test('filter all element under threshold "50"', async ({ page, annotationListPage }) => {
        const threshold = 50;
        const predictions = segmentationPredictionsResponse.annotations;
        await page.goto(segmentationUrl);

        const visiblePredictions = predictions.filter((annotation) =>
            annotation.labels.every((label) => label.probability > threshold / 100)
        );

        await annotationListPage.expectTotalAnnotationsToBe(segmentationPredictionsResponse.annotations.length);

        await annotationListPage.moveThresholdSliderUp(threshold);
        //click outside
        await page.getByLabel(/^Selection$/).click();

        await annotationListPage.expectTotalAnnotationsToBe(visiblePredictions.length);
    });
});
