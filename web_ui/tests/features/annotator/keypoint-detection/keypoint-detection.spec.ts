// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { checkKeypointTools, annotatorTest as test } from '../../../fixtures/annotator-test';
import {
    annotatorUrl,
    labels,
    predictionAnnotationsResponse,
    project,
    userAnnotationsResponse,
} from '../../../mocks/keypoint-detection/mocks';

const assertAnnotationVisibility = async (page: Page, labelName: string) => {
    await expect(page.getByTestId('annotation-list-accordion').getByText(labelName, { exact: true })).toBeVisible();
    await expect(page.getByLabel(`Resize keypoint ${labelName} anchor`)).toBeVisible();
};

const assertPredictionVisibility = async (page: Page, labelName: string, score: number) => {
    await expect(page.getByTestId(`pose label - ${labelName}`)).toBeVisible();
    await expect(page.getByText(`${labelName}(${score}%)`)).toBeVisible();
};

test.describe(`keypoint detection`, () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));

        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userAnnotationsResponse)));
        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            return res(ctx.json(predictionAnnotationsResponse));
        });
    });

    test('predictions as initial annotations', async ({ page, annotatorPage, registerApiResponse }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
        );

        await page.goto(annotatorUrl);

        await checkKeypointTools(page);
        await annotatorPage.selectAnnotationMode();

        await assertPredictionVisibility(page, labels.head.name, 17);
        await assertPredictionVisibility(page, labels.back.name, 10);
        await assertPredictionVisibility(page, labels.back2.name, 12);
        await assertPredictionVisibility(page, labels.leftFrontLeg.name, 11);
        await assertPredictionVisibility(page, labels.rightFrontLeg.name, 13);
        await assertPredictionVisibility(page, labels.leftBackLeg.name, 14);
        await assertPredictionVisibility(page, labels.rightBackLeg.name, 16);

        await annotatorPage.selectPredictionMode();

        await page.getByLabel('Use predictions').click();
        await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Merge' })).not.toBeInViewport();
    });

    test('Annotations and predictions', async ({ page, annotatorPage }) => {
        await page.goto(annotatorUrl);

        await checkKeypointTools(page);

        await page.getByTestId('transform-zoom-canvas').locator('rect').click();

        await assertAnnotationVisibility(page, labels.head.name);
        await assertAnnotationVisibility(page, labels.back.name);
        await assertAnnotationVisibility(page, labels.back2.name);
        await assertAnnotationVisibility(page, labels.leftFrontLeg.name);
        await assertAnnotationVisibility(page, labels.rightFrontLeg.name);
        await assertAnnotationVisibility(page, labels.leftBackLeg.name);
        await assertAnnotationVisibility(page, labels.rightBackLeg.name);

        await annotatorPage.selectPredictionMode();

        await assertPredictionVisibility(page, labels.head.name, 17);
        await assertPredictionVisibility(page, labels.back.name, 10);
        await assertPredictionVisibility(page, labels.back2.name, 12);
        await assertPredictionVisibility(page, labels.leftFrontLeg.name, 11);
        await assertPredictionVisibility(page, labels.rightFrontLeg.name, 13);
        await assertPredictionVisibility(page, labels.leftBackLeg.name, 14);
        await assertPredictionVisibility(page, labels.rightBackLeg.name, 16);
    });

    test('rotate annotations', async ({ page, templateManagerPage }) => {
        await page.goto(annotatorUrl);
        await checkKeypointTools(page);
        await page.getByTestId('transform-zoom-canvas').locator('rect').click();

        const headPosition = await templateManagerPage.getPosition(page.getByLabel('Resize keypoint head anchor'));
        const rotateAnchorPosition = await templateManagerPage.getPosition(page.getByLabel('rotate anchor'));

        await page.mouse.move(rotateAnchorPosition.x, rotateAnchorPosition.y);
        await page.mouse.down({ button: 'left' });

        // rotate 180
        await page.mouse.move(rotateAnchorPosition.x + 100, rotateAnchorPosition.y);
        await page.mouse.move(rotateAnchorPosition.x, rotateAnchorPosition.y + 1000, { steps: 30 });

        await expect(page.getByLabel('rotation group')).toHaveAttribute('transform', /rotate\(180, \d+, \d+\)/);
        await page.mouse.up({ button: 'left' });

        const headPositionAfterRotate = await templateManagerPage.getPosition(
            page.getByLabel('Resize keypoint head anchor')
        );

        expect(headPosition).not.toEqual(headPositionAfterRotate);
    });
});
