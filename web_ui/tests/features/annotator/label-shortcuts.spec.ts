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

import { Rect } from '../../../src/core/annotations/shapes.interface';
import { ShapeType } from '../../../src/core/annotations/shapetype.enum';
import { OpenApiResponseBody } from '../../../src/core/server/types';
import { expect } from '../../fixtures/base-test';
import { getAnnotationListItems } from '../../utils/selectors';
import { annotatorTest as test } from './../../fixtures/annotator-test';

const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/62946c61003ddb3967f14750/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa';

test.describe('Label shortcuts behaviour', () => {
    test.beforeEach(async ({ registerApiExample, registerApiResponse }) => {
        registerApiExample('GetProjectInfo', 'Detection classification response');
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => {
            return res(ctx.status(404));
        });
    });

    test('It can pin & unpin more labels', async ({ page, labelShortcutsPage }) => {
        await page.goto(annotatorUrl);
        await labelShortcutsPage.openLabelShortcutsMenu();
        await labelShortcutsPage.pinLabel('Seven');
        await labelShortcutsPage.closeLabelShortcutsMenu();

        await expect(await labelShortcutsPage.getPinnedLabelLocator('Seven')).toBeVisible();

        await labelShortcutsPage.openLabelShortcutsMenu();
        await labelShortcutsPage.unpinLabel('Seven');
        await labelShortcutsPage.closeLabelShortcutsMenu();

        await expect(await labelShortcutsPage.getPinnedLabelLocator('Seven')).toBeHidden();
    });

    test('applies a label', async ({ page, labelShortcutsPage }) => {
        await page.goto(annotatorUrl);
        const selectAnnotation = page.getByRole('checkbox', {
            name: /Select annotation 6b3b8453-92a2-41ef-9725-63badb218504/,
        });
        await selectAnnotation.click();

        const heartsButton = await labelShortcutsPage.getPinnedLabelLocator('Hearts');
        await expect(heartsButton).toBeVisible();

        // Adds a label when clicked
        await heartsButton.click();
        await expect(
            page.getByRole('listitem', { name: 'Annotation with id 6b3b8453-92a2-41ef-9725-63badb218504' })
        ).toContainText('Hearts');

        // It updates the default label
        await expect(page.getByLabel('Selected default label')).toContainText('Hearts');

        // Removes the label when applied again
        await heartsButton.click();
        await expect(
            page.getByRole('listitem', { name: 'Annotation with id 6b3b8453-92a2-41ef-9725-63badb218504' })
        ).not.toContainText('Hearts');
    });

    test.describe('confirms annotations if the user selects a label', () => {
        test('with interactive segmentation', async ({
            page,
            labelShortcutsPage,
            registerApiExample,
            annotatorPage,
            interactiveSegmentationTool,
        }) => {
            registerApiExample('GetProjectInfo', 'Segmentation response');

            const shape: Rect = { x: 500, y: 500, width: 200, height: 100, shapeType: ShapeType.Rect };
            const objectLabelButton = await labelShortcutsPage.getPinnedLabelLocator('object');

            await page.goto(annotatorUrl);
            await annotatorPage.deleteAllAnnotations();

            await interactiveSegmentationTool.selectTool();

            await page.mouse.click(shape.x + 200, shape.y);

            await expect(page.getByTestId('point-positive-0')).toBeVisible();

            // Adds a label when clicked
            await objectLabelButton.click();

            await expect(getAnnotationListItems(page)).toHaveCount(1);

            await expect(getAnnotationListItems(page).first()).toHaveText('object');
        });

        test('with detection assistant (SSIM)', async ({
            page,
            labelShortcutsPage,
            registerApiExample,
            annotatorPage,
            detectionAssistantTool,
        }) => {
            registerApiExample('GetProjectInfo', 'Segmentation response');

            const shape = { x: 10, y: 20, width: 200, height: 100 };
            const objectLabelButton = await labelShortcutsPage.getPinnedLabelLocator('object');

            await page.goto(annotatorUrl);
            await annotatorPage.deleteAllAnnotations();

            await detectionAssistantTool.selectTool();
            await detectionAssistantTool.drawBoundingBox(shape);

            await expect(page.getByRole('button', { name: 'accept ssim annotation' })).toBeVisible();

            // Adds a label when clicked
            await objectLabelButton.click();

            await expect(getAnnotationListItems(page)).toHaveCount(6);
            await expect(getAnnotationListItems(page).first()).toHaveText('object');
        });

        test('with quick selection (grabcut)', async ({
            page,
            labelShortcutsPage,
            registerApiExample,
            annotatorPage,
            quickSelectionTool,
        }) => {
            registerApiExample('GetProjectInfo', 'Segmentation response');

            const shape: Rect = { x: 400, y: 300, width: 100, height: 80, shapeType: ShapeType.Rect };
            const objectLabelButton = await labelShortcutsPage.getPinnedLabelLocator('object');

            await page.goto(annotatorUrl);
            await annotatorPage.deleteAllAnnotations();

            await quickSelectionTool.selectTool();
            await quickSelectionTool.drawBoundingBox(shape);

            await expect(page.getByLabel('loading-roi-rect')).toBeHidden();

            // Adds a label when clicked
            await objectLabelButton.click();

            await expect(getAnnotationListItems(page)).toHaveCount(1);
            await expect(getAnnotationListItems(page).first()).toHaveText('object');
        });
    });

    test('keyboard shortcuts', async ({ page, registerApiResponse, openApi }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            const { mock } = openApi.mockResponseForOperation('GetProjectInfo', {
                example: 'Detection classification response',
            }) as {
                mock: OpenApiResponseBody<'GetProjectInfo'>;
            };

            // @ts-expect-error types from OpenAPI spec aren't properly set
            mock.pipeline.tasks[3].labels[0].hotkey = 'ctrl+h';
            // @ts-expect-error types from OpenAPI spec aren't properly set
            mock.pipeline.tasks[3].labels[1].hotkey = 'ctrl+e';

            return res(ctx.json(mock));
        });

        await page.goto(annotatorUrl);

        const selectAnnotation = page.getByRole('checkbox', {
            name: 'Select annotation 6b3b8453-92a2-41ef-9725-63badb218504',
        });
        await selectAnnotation.click();

        // Applies the label
        await page.keyboard.press('Control+h');
        await expect(
            page.getByRole('listitem', { name: 'Annotation with id 6b3b8453-92a2-41ef-9725-63badb218504' })
        ).toContainText('Hearts');
        await expect(page.getByLabel('Selected default label')).toContainText('Hearts');

        // Overwrites the label
        await page.keyboard.press('Control+e');
        await expect(
            page.getByRole('listitem', { name: 'Annotation with id 6b3b8453-92a2-41ef-9725-63badb218504' })
        ).toContainText('Diamonds');
        await expect(page.getByLabel('Selected default label')).toContainText('Diamonds');

        // Removes the label
        await page.keyboard.press('Control+e');
        await expect(
            page.getByRole('listitem', { name: 'Annotation with id 6b3b8453-92a2-41ef-9725-63badb218504' })
        ).not.toContainText('Diamonds');
        await expect(page.getByLabel('Selected default label')).toContainText('Diamonds');
    });
});

test.describe('Task chain "Detection -> Classification" example', () => {
    test.beforeEach(async ({ registerApiExample }) => {
        registerApiExample('GetProjectInfo', 'Detection classification response');
    });

    test('All tasks: All labels are shown for all tasks mode', async ({ page, labelShortcutsPage }) => {
        await page.goto(annotatorUrl);

        await expect(await labelShortcutsPage.getPinnedLabelLocator('Card')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('No object')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Hearts')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Diamonds')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Spades')).toBeVisible();
    });

    test('Detection: Only detection labels are shown for detection task', async ({ page, labelShortcutsPage }) => {
        await page.goto(`${annotatorUrl}?task-id=62946c61003ddb3967f1474d`);

        await expect(await labelShortcutsPage.getPinnedLabelLocator('Card')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('No object')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Hearts')).toBeHidden();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Diamonds')).toBeHidden();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Spades')).toBeHidden();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Seven')).toBeHidden();
    });

    test('Classification: Only classification labels are shown for classification task', async ({
        page,
        labelShortcutsPage,
    }) => {
        await page.goto(`${annotatorUrl}?task-id=62946c61003ddb3967f1474f`);

        await expect(await labelShortcutsPage.getPinnedLabelLocator('Card')).toBeHidden();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('No object')).toBeHidden();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Hearts')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Diamonds')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Spades')).toBeVisible();
        await expect(await labelShortcutsPage.getPinnedLabelLocator('Seven')).toBeVisible();
    });
});
