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

import { expect, Locator, Page } from '@playwright/test';

import { SHAPE_TYPE_DTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { annotatorUrl, media, project as orientedDetectionProejct } from '../../../mocks/detection-oriented/mocks';
import { project } from '../../../mocks/segmentation/mocks';
import { clickAndMove } from '../../../utils/mouse';
import { expectCircleShape, expectRectShape } from '../expect';

const getTemplateLocator = (page: Page) => page.locator('svg').getByLabel('template');
const getPredictionsLocator = (page: Page) => page.locator('svg').getByLabel('prediction');
const getMergeDuplicateSwitchLocator = (page: Page) => page.locator('input[role="switch"]');
const numberOfMatchesLocator = (page: Page) =>
    page.getByRole('button', { name: 'Detection tool threshold slider button' });
const numberOfMatchesSliderLocator = (page: Page) => page.locator('[role="presentation"] input[type=range]');

const getShapeLocator = (page: Page, type: string) => page.getByLabel('annotations').locator(type);

const waitForSSIM = async (button: Locator) => {
    await expect(button).toBeEnabled({ timeout: 10000 });
};

test.describe('Detection assistant', () => {
    test.beforeEach(async ({ page, annotatorPath, detectionAssistantTool, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.status(200), ctx.json(project)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.status(204)));

        await page.goto(annotatorPath);
        await detectionAssistantTool.selectTool();
    });
    test.describe('ShapeType: Rect', () => {
        const shape = { x: 10, y: 20, width: 200, height: 100 };
        const expectedTotalMatches = 5;

        test('Detected items slider should be visible only when there are annotations in the result', async ({
            page,
            detectionAssistantTool,
        }) => {
            await expect(numberOfMatchesLocator(page)).toBeHidden();

            await detectionAssistantTool.drawBoundingBox(shape);
            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            await expect(numberOfMatchesLocator(page)).toBeVisible();
        });

        test('draw template shows the template drawn', async ({ page, detectionAssistantTool }) => {
            await detectionAssistantTool.drawBoundingBox(shape);
            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const templateLocator = getTemplateLocator(page);

            await expectRectShape(templateLocator, shape);
        });

        test('shows detection tool predictions', async ({ page, detectionAssistantTool }) => {
            await detectionAssistantTool.drawBoundingBox(shape);
            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const predictionsLocator = getPredictionsLocator(page);

            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());
            await expect(predictionsLocator).toHaveCount(expectedTotalMatches);
            await expect(detectionAssistantTool.numberOfMatchesFieldLocator()).toHaveValue(
                `${expectedTotalMatches + 1}`
            );
        });

        test('change number of prediction using number slider input', async ({ page, detectionAssistantTool }) => {
            await detectionAssistantTool.drawBoundingBox(shape);
            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const predictionsLocator = getPredictionsLocator(page);
            const numberOfItemSliderCounter = detectionAssistantTool.numberOfMatchesFieldLocator();

            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());
            await expect(predictionsLocator).toHaveCount(expectedTotalMatches);
            await expect(numberOfItemSliderCounter).toHaveValue(`${expectedTotalMatches + 1}`);

            //type more than maximum number of predictions - expect 6
            await detectionAssistantTool.changeNumberOfAnnotations(56);
            await expect(numberOfItemSliderCounter).toHaveValue(`${expectedTotalMatches + 1}`);

            //clear field - nothing changes in predictions
            await numberOfItemSliderCounter.clear();
            await expect(predictionsLocator).toHaveCount(expectedTotalMatches);

            //type less than minimum - expect 1(minimum)
            await detectionAssistantTool.changeNumberOfAnnotations(0);
            await expect(numberOfItemSliderCounter).toHaveValue('1');

            await detectionAssistantTool.changeNumberOfAnnotations(4);
            await expect(numberOfItemSliderCounter).toHaveValue('4');
            await expect(predictionsLocator).toHaveCount(3); // 3 predictions + 1 template
        });

        test('sliding the number of annotations reduces the shown predictions', async ({
            page,
            detectionAssistantTool,
        }) => {
            await detectionAssistantTool.drawBoundingBox(shape);
            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            await numberOfMatchesLocator(page).click();

            const dragNode = numberOfMatchesSliderLocator(page);
            const templateLocator = getTemplateLocator(page);

            await expectRectShape(templateLocator, shape);

            const boundingBox = await dragNode.boundingBox();

            if (!boundingBox) {
                throw 'Bounding box not found';
            }

            await clickAndMove(page, boundingBox, { x: boundingBox.x - 40, y: boundingBox.y });

            const predictionsLocator = getPredictionsLocator(page);

            const numberOfItemSliderCounter = detectionAssistantTool.numberOfMatchesFieldLocator();
            const expectedMatches = Number.parseInt(await numberOfItemSliderCounter.inputValue());

            await expect(predictionsLocator).toHaveCount(expectedMatches - 1);
        });

        test('without auto merge duplicates adds predictions that overlap existing annotations', async ({
            page,
            detectionAssistantTool,
            boundingBoxTool,
        }) => {
            const secondaryShape = { x: 306, y: 16, width: 200, height: 100 };

            await boundingBoxTool.selectTool();
            await boundingBoxTool.drawBoundingBox(secondaryShape);
            await detectionAssistantTool.selectTool();
            await detectionAssistantTool.drawBoundingBox(shape);
            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const predictionsLocator = getPredictionsLocator(page);

            // With merge enabled expecting one less
            await expect(predictionsLocator).toHaveCount(expectedTotalMatches - 1);
            await getMergeDuplicateSwitchLocator(page).click();
            await expect(predictionsLocator).toHaveCount(expectedTotalMatches);
        });

        test('accept results gives all shapes as new rect annotations', async ({ page, detectionAssistantTool }) => {
            const numberOfItemSliderCounter = detectionAssistantTool.numberOfMatchesFieldLocator();
            await detectionAssistantTool.drawBoundingBox(shape);
            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const expectedMatches = Number.parseInt(await numberOfItemSliderCounter.inputValue());

            expect(expectedMatches).toBeGreaterThan(1);

            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            await detectionAssistantTool.acceptAnnotation();
            await expect(getShapeLocator(page, 'rect')).toHaveCount(expectedMatches);
        });

        test('Undo and redo SSIM', async ({ detectionAssistantTool, annotationListPage, undoRedo }) => {
            const numberOfItemSliderCounter = detectionAssistantTool.numberOfMatchesFieldLocator();
            await detectionAssistantTool.drawBoundingBox(shape);
            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const expectedMatches = Number.parseInt(await numberOfItemSliderCounter.inputValue());

            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            await detectionAssistantTool.acceptAnnotation();

            await annotationListPage.expectTotalAnnotationsToBe(expectedMatches);

            await undoRedo.undoUsingButton();

            await annotationListPage.expectTotalAnnotationsToBe(0);

            await undoRedo.redoUsingButton();

            await annotationListPage.expectTotalAnnotationsToBe(expectedMatches);

            await undoRedo.undoUsingShortcut();

            await annotationListPage.expectTotalAnnotationsToBe(0);

            await undoRedo.redoUsingShortcut();

            await annotationListPage.expectTotalAnnotationsToBe(expectedMatches);
        });

        test('Selects SSIM tool using hotkey', async ({ page }) => {
            // Change to circle tool first
            await page.keyboard.press('c');

            await expect(page.locator('role=button[name="Circle"]')).toHaveAttribute('aria-pressed', 'true');

            await page.keyboard.press('d');

            await expect(page.locator('role=button[name="Detection assistant"]')).toHaveAttribute(
                'aria-pressed',
                'true'
            );
        });

        test('Should use the correct cursor', async ({ page, detectionAssistantTool }) => {
            await detectionAssistantTool.selectTool();
            await page.mouse.move(100, 100);

            expect(await page.locator('[role=editor]').getAttribute('style')).toContain('selection');
        });

        test('Should display the correct tooltips', async ({ page, detectionAssistantTool }) => {
            await detectionAssistantTool.selectTool();

            const boundingBoxModeButton = page.getByLabel('Bounding box mode');
            const circleModeButton = page.getByLabel('Circle mode');

            await expect(boundingBoxModeButton).toBeVisible();
            await boundingBoxModeButton.hover();
            await expect(page.getByText('Bounding box mode')).toBeVisible();

            await circleModeButton.hover();
            await expect(page.getByText('Circle mode')).toBeVisible();
        });
    });

    test.describe('circle', () => {
        const shape = { x: 100, y: 100, r: 100 };

        test('draws a circle template', async ({ page, detectionAssistantTool }) => {
            await detectionAssistantTool.selectCircleMode();
            await detectionAssistantTool.drawCircle(shape);

            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const templateLocator = getTemplateLocator(page);

            await expectCircleShape(templateLocator, shape);
        });

        test('finds circle template', async ({ page, detectionAssistantTool }) => {
            await detectionAssistantTool.selectCircleMode();
            await detectionAssistantTool.drawCircle(shape);

            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const predictionsLocator = getPredictionsLocator(page);
            const numberOfItemSliderCounter = detectionAssistantTool.numberOfMatchesFieldLocator();
            const expectedMatches = Number.parseInt(await numberOfItemSliderCounter.inputValue());

            await expect(predictionsLocator).toHaveCount(expectedMatches - 1);
        });

        test('accept results gives all shapes as new circle annotations', async ({ page, detectionAssistantTool }) => {
            const numberOfItemSliderCounter = detectionAssistantTool.numberOfMatchesFieldLocator();
            await detectionAssistantTool.selectCircleMode();
            await detectionAssistantTool.drawCircle(shape);

            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            const expectedMatches = Number.parseInt(await numberOfItemSliderCounter.inputValue());

            expect(expectedMatches).toBeGreaterThan(1);

            await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

            await detectionAssistantTool.acceptAnnotation();
            await expect(getShapeLocator(page, 'circle')).toHaveCount(expectedMatches);
        });
    });
});

test.describe('Oriented detection projects', () => {
    const shape = { x: 10, y: 20, width: 200, height: 100 };

    test('Outputs rotated rectangles when used in a oriented detection project', async ({
        page,
        detectionAssistantTool,
        registerApiResponse,
    }) => {
        const storedAnnotationsShapeTypes: string[] = [];

        registerApiResponse('CreateImageAnnotation', (req, res, ctx) => {
            req.body.annotations.forEach((annotation) => storedAnnotationsShapeTypes.push(annotation.shape.type));

            return res(ctx.status(200), ctx.json({ annotation_state_per_task: [], annotations: [] }));
        });
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(orientedDetectionProejct)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(404)));
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.status(404)));

        await page.goto(annotatorUrl);
        await detectionAssistantTool.selectTool();

        await expect(numberOfMatchesLocator(page)).toBeHidden();

        await detectionAssistantTool.drawBoundingBox(shape);
        await waitForSSIM(await detectionAssistantTool.getAcceptAnnotationButton());

        await expect(numberOfMatchesLocator(page)).toBeVisible();
        await (await detectionAssistantTool.getAcceptAnnotationButton()).click();

        await page.getByRole('button', { name: /submit annotations/i }).click();

        await expect(() => {
            return expect(storedAnnotationsShapeTypes).toHaveLength(6);
        }).toPass({ timeout: 1000 });

        storedAnnotationsShapeTypes.forEach((shapeType) => {
            expect(shapeType).toBe(SHAPE_TYPE_DTO.ROTATED_RECTANGLE);
        });
    });
});
