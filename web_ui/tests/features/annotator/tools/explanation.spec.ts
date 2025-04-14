// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { annotatorUrl, media, project, userAnnotationsResponse } from '../../../mocks/segmentation/mocks';
import { waitForLoadingToBeFinished } from '../../../utils/assertions';

test.describe('Explanation', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));

        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userAnnotationsResponse)));
    });

    test('shows explanation image on prediction shape position', async ({ page, explanation, registerApiResponse }) => {
        const mapPosition = { top: `0px`, left: `0px` };

        registerApiResponse('CreateImageAnnotation', (req, res, ctx) =>
            res(ctx.status(200), ctx.json({ annotation_state_per_task: [], ...req.body }))
        );

        await page.goto(`${annotatorUrl}?mode=predictions`);

        await explanation.expectToHaveExplanation(mapPosition);
    });

    test('change opacity', async ({ page, explanation, registerApiResponse }) => {
        registerApiResponse('CreateImageAnnotation', (req, res, ctx) =>
            res(ctx.status(200), ctx.json({ annotation_state_per_task: [], ...req.body }))
        );

        await page.goto(`${annotatorUrl}?mode=predictions`);

        await explanation.activateTool();

        const opacitySliderButton = await explanation.getOpacitySliderButton();
        await expect(opacitySliderButton).toBeEnabled();
        await opacitySliderButton.click();

        for await (const num of [-100, 50, 100]) {
            const newValue = await explanation.moveOpacitySlider(num);
            await explanation.expectCanvasHasOpacityOf(Number(newValue) / 100);
        }
    });

    test('Check if labels shortcuts are disabled when explanation is displayed', async ({
        page,
        explanation,
        registerApiResponse,
        labelShortcutsPage,
    }) => {
        registerApiResponse('CreateImageAnnotation', (req, res, ctx) =>
            res(ctx.status(200), ctx.json({ annotation_state_per_task: [], ...req.body }))
        );

        await page.goto(`${annotatorUrl}?mode=predictions`);
        await waitForLoadingToBeFinished(page);
        await explanation.activateTool();

        await expect(await labelShortcutsPage.getPinnedLabelLocator('horse')).toBeDisabled();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('donkey')).toBeDisabled();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('saddled')).toBeDisabled();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('unsaddled')).toBeDisabled();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('No class')).toBeDisabled();
    });
});
