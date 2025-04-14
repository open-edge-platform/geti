// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Locator, Page } from '@playwright/test';
import isEmpty from 'lodash/isEmpty';

import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { annotatorUrl, project } from '../../../mocks/segmentation/mocks';
import { expectShapeColor } from '../../../utils/assertions';
import { getBackgroundColor, getFillColor } from '../../../utils/dom';
import { clickAndMove, withRelative } from '../../../utils/mouse';
import { getSubmitButton } from '../../../utils/selectors';

const defaultShapeColor = 'var(--energy-blue)';

const expectNewLabeledAnnotation = async (page: Page, labelButton: Locator) => {
    const labelColor = await getBackgroundColor(labelButton.locator('div').first());
    const annotationListFirstItem = page.getByLabel('edit-annotations', { exact: true }).getByLabel('labels');
    const annotationLabelColor = await getBackgroundColor(annotationListFirstItem.locator('li'));
    const annotationLabelText = (await annotationListFirstItem.textContent()) ?? '';
    const annotatorColor = await getFillColor(
        page.getByLabel('edit-annotations').getByLabel('Drag to move shape').locator('> g')
    );

    expect(labelColor).toBe(annotationLabelColor);
    expect(labelColor).toBe(annotatorColor);
    await expect(labelButton).toHaveText(annotationLabelText);
};

const waitForGrabcutResponse = async (page: Page) =>
    await expect(page.getByLabel('loading-roi-rect')).toBeHidden({ timeout: 30_000 });

const expectToiToBeRemoved = async (page: Page) => expect(page.getByLabel('roi-rect')).toBeHidden();

const getGrabcutPolygon = (page: Page) => page.getByLabel('grabcut-polygon');

test.describe('Quick selection', () => {
    test.beforeEach(async ({ page, annotatorPath, quickSelectionTool, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.status(200), ctx.json(project)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.status(204)));

        await page.goto(annotatorPath);
        await quickSelectionTool.selectTool();
    });

    test('draw and accept annotation', async ({ page, quickSelectionTool, labelShortcutsPage }) => {
        await (await labelShortcutsPage.getPinnedLabelLocator('horse')).click();
        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });
        await expect(getSubmitButton(page)).toBeDisabled();

        await waitForGrabcutResponse(page);
        const newPolygon = getGrabcutPolygon(page);
        const cardColor = '#0015ffff';
        await expectShapeColor(newPolygon, cardColor);

        await quickSelectionTool.acceptAnnotation();

        await expect(getSubmitButton(page)).toBeEnabled();

        const labelButton = page.locator('#canvas-labels > div button').first();
        await expectNewLabeledAnnotation(page, labelButton);
    });

    test('it changes the accuracy of grabcut', async ({ page, quickSelectionTool }) => {
        await quickSelectionTool.changeSensitivity(-100);
        await page.mouse.click(0, 0);

        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });
        await expect(getSubmitButton(page)).toBeDisabled();
        await waitForGrabcutResponse(page);

        await quickSelectionTool.changeSensitivity(50);
        await page.mouse.click(0, 0);
        await waitForGrabcutResponse(page);

        await quickSelectionTool.changeSensitivity(50);
        await page.mouse.click(0, 0);
        await waitForGrabcutResponse(page);

        await quickSelectionTool.changeSensitivity(50);
        await page.mouse.click(0, 0);
        await waitForGrabcutResponse(page);

        await quickSelectionTool.changeSensitivity(50);
        await page.mouse.click(0, 0);
        await waitForGrabcutResponse(page);

        await quickSelectionTool.acceptAnnotation();
        await expect(getSubmitButton(page)).toBeEnabled();
    });

    test('draw new `rect` accepts the previous unaccepted shape', async ({
        page,
        quickSelectionTool,
        annotationListPage,
    }) => {
        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });

        await annotationListPage.expectTotalAnnotationsToBe(0);
        await waitForGrabcutResponse(page);

        await quickSelectionTool.drawBoundingBox({ x: 30, y: 110, width: 180, height: 110 });
        await annotationListPage.expectTotalAnnotationsToBe(1);

        await waitForGrabcutResponse(page);
        await quickSelectionTool.acceptAnnotation();
        await annotationListPage.expectTotalAnnotationsToBe(2);
    });

    test('draw and reject annotation', async ({ page, quickSelectionTool, annotationListPage }) => {
        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });
        await expect(getSubmitButton(page)).toBeDisabled();
        await waitForGrabcutResponse(page);

        await expect(getGrabcutPolygon(page)).toBeVisible();
        await quickSelectionTool.rejectAnnotation();

        await annotationListPage.expectTotalAnnotationsToBe(0);
        await expect(getSubmitButton(page)).toBeEnabled();
        await expect(getGrabcutPolygon(page)).toBeHidden();
    });

    test('markers drawn outside roi are ignored', async ({ page, quickSelectionTool }) => {
        const relative = await withRelative(page);
        const roi = { x: 30, y: 110, width: 180, height: 110 };
        await quickSelectionTool.drawBoundingBox(roi);

        await page.getByLabel('Subtract from selection').click();
        const foreground = {
            startPoint: relative(roi.x + roi.width + 10, roi.y),
            endPoint: relative(roi.x + roi.width + 10, roi.y + roi.height),
        };
        await clickAndMove(page, foreground.startPoint, foreground.endPoint);

        await page.getByLabel('Add to selection').click();
        const background = {
            startPoint: relative(roi.x, roi.y + roi.height + 10),
            endPoint: relative(roi.x + roi.width + 10, roi.y + roi.height + 10),
        };
        await clickAndMove(page, background.startPoint, background.endPoint);

        await expect(page.getByLabel('background-marker')).toBeHidden();
        await expect(page.getByLabel('foreground-marker')).toBeHidden();
    });

    test("Annotation's region of interest has dashed stroke and no background", async ({
        page,
        quickSelectionTool,
    }) => {
        const roi = { x: 30, y: 110, width: 180, height: 110 };
        await quickSelectionTool.drawBoundingBox(roi);

        const roiRect = page.getByLabel('roi-rect');

        await expect(roiRect).toHaveAttribute('fill-opacity', '0');
        await expect(roiRect).toHaveAttribute('stroke-dasharray', 'calc(10 / var(--zoom-level))');
    });

    test('Undo redo Quick selection', async ({
        quickSelectionTool,
        page,
        undoRedo,
        annotationListPage,
        labelShortcutsPage,
    }) => {
        await (await labelShortcutsPage.getPinnedLabelLocator('horse')).click();

        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });
        await expect(getSubmitButton(page)).toBeDisabled();

        await waitForGrabcutResponse(page);
        const newPolygon = getGrabcutPolygon(page);
        const cardColor = '#0015ffff';
        await expectShapeColor(newPolygon, cardColor);

        await quickSelectionTool.acceptAnnotation();

        const labelButton = page.locator('#canvas-labels > div button').first();
        await expectNewLabeledAnnotation(page, labelButton);

        await undoRedo.undoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(1);

        await undoRedo.undoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(1);
        await expectNewLabeledAnnotation(page, labelButton);
    });

    test('Should use the correct cursor', async ({ page, quickSelectionTool }) => {
        await quickSelectionTool.selectTool();

        await expect(page.getByLabel('New selection')).toBeVisible();
        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });

        await expect(page.getByLabel('loading-roi-rect')).toBeHidden();
        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('selection');

        const addToSelectionButton = page.getByLabel('Add to selection');
        await addToSelectionButton.click();
        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('pencil-plus');

        const subtractFromSelectionButton = page.getByLabel('Subtract from selection');
        await subtractFromSelectionButton.click();
        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('pencil-minus');
    });

    test('Should display the correct tooltips', async ({ page, quickSelectionTool }) => {
        await quickSelectionTool.selectTool();
        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });

        const newSelectionButton = page.getByLabel('New selection');
        await newSelectionButton.hover();
        await expect(page.getByText('New selection')).toBeVisible();

        const addToSelectionButton = page.getByLabel('Add to selection');
        await addToSelectionButton.hover();
        await expect(page.getByText('Add to selection')).toBeVisible();

        const subtractFromSelectionButton = page.getByLabel('Subtract from selection');
        await subtractFromSelectionButton.hover();
        await expect(page.getByText('Subtract from selection')).toBeVisible();
    });
});

test.describe('Quick selection with open api as a backend', () => {
    test('Multiple labels: click label button shortcut accepts and labels the annotation', async ({
        page,
        registerApiResponse,
        quickSelectionTool,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.status(200), ctx.json(project)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(200), ctx.json({ annotations: [] })));

        await page.goto(annotatorUrl);
        await quickSelectionTool.selectTool();

        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });
        await waitForGrabcutResponse(page);
        await expectShapeColor(getGrabcutPolygon(page), defaultShapeColor);

        const labelButton = page.locator('#canvas-labels > div button').first();
        await labelButton.click();
        await expectToiToBeRemoved(page);

        await expectNewLabeledAnnotation(page, labelButton);
    });

    test('Single label: annotation is labeled automatically', async ({
        page,
        registerApiResponse,
        quickSelectionTool,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            const [task] = project.pipeline.tasks.filter(({ labels }) => !isEmpty(labels));
            const [label] = task.labels ?? [];
            return res(
                ctx.status(200),
                ctx.json({
                    ...project,
                    pipeline: {
                        ...project.pipeline,
                        tasks: [{ ...task, labels: [label] }],
                    },
                })
            );
        });
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(200), ctx.json({ annotations: [] })));

        await page.goto(annotatorUrl);
        await quickSelectionTool.selectTool();

        await quickSelectionTool.drawBoundingBox({ x: 200, y: 100, width: 600, height: 500 });
        const labelButton = page.locator('#canvas-labels > div button').first();
        const labelColor = await getBackgroundColor(labelButton.locator('div').first());
        await waitForGrabcutResponse(page);

        const grabcutPolygonColor = await getFillColor(getGrabcutPolygon(page));

        expect(labelColor).toBe(grabcutPolygonColor);

        await quickSelectionTool.acceptAnnotation();

        await expectNewLabeledAnnotation(page, labelButton);
    });
});
