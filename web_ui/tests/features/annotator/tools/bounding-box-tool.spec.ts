// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { project } from '../../../mocks/segmentation/mocks';
import { clickAndMove, withRelative } from '../../../utils/mouse';
import {
    clearDefaultLabel,
    expectLabelIsAssignedToDrawnShape,
    expectPreselectedLabelIsAssignedToDrawnShape,
    expectRectShape,
} from '../expect';

const getShapeLocator = (page: Page) =>
    page.getByLabel('edit-annotations').getByLabel('Drag to move shape').locator('rect');

test.describe('Bounding box', () => {
    const shape = { x: 10, y: 20, width: 300, height: 300 };
    const halfShape = { width: shape.width / 2, height: shape.height / 2 };
    const centerShape = { x: shape.x + halfShape.width, y: shape.y + halfShape.height };

    const labelName = 'horse';

    test.beforeEach(async ({ page, annotatorPath, boundingBoxTool, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.status(200), ctx.json(project)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.status(204)));

        await page.goto(annotatorPath);
        await boundingBoxTool.selectTool();
    });

    test('Draw bounding box', async ({ page, boundingBoxTool }) => {
        await boundingBoxTool.drawBoundingBox(shape);
        const shapeLocator = getShapeLocator(page);

        await expectRectShape(shapeLocator, shape);
    });

    test('Move bounding box', async ({ page, boundingBoxTool, selectionTool }) => {
        await boundingBoxTool.drawBoundingBox(shape);
        await selectionTool.selectTool();
        const relative = await withRelative(page);

        const startPoint = relative(centerShape.x, centerShape.y);
        const endPoint = relative(centerShape.x + halfShape.width, shape.y + halfShape.height);

        await clickAndMove(page, startPoint, endPoint);
        const shapeLocator = getShapeLocator(page);

        await expectRectShape(shapeLocator, { ...shape, x: shape.x + halfShape.width });
    });

    test('Resize bounding box', async ({ page, boundingBoxTool }) => {
        await boundingBoxTool.drawBoundingBox(shape);
        const relative = await withRelative(page);

        const southEastResizeAnchor = relative(shape.x + shape.width, shape.y + shape.height);
        const endPoint = relative(shape.x + halfShape.width, shape.y + halfShape.height);

        await clickAndMove(page, southEastResizeAnchor, endPoint);
        const shapeLocator = getShapeLocator(page);

        await expectRectShape(shapeLocator, { ...shape, width: halfShape.width, height: halfShape.height });
    });

    test('Resize bounding box with "selection tool"', async ({ page, boundingBoxTool, selectionTool }) => {
        await boundingBoxTool.drawBoundingBox(shape);
        await selectionTool.selectTool();
        const relative = await withRelative(page);

        const northWestResizeAnchor = relative(shape.x, shape.y);
        const endPoint = relative(shape.x + halfShape.width, shape.y + halfShape.height);

        await clickAndMove(page, northWestResizeAnchor, endPoint);
        const shapeLocator = getShapeLocator(page);

        await expectRectShape(shapeLocator, {
            x: shape.x + halfShape.width,
            y: shape.y + halfShape.height,
            width: halfShape.width,
            height: halfShape.height,
        });
    });

    test('Add label to bounding box', async ({ page, boundingBoxTool }) => {
        await clearDefaultLabel(page);
        await boundingBoxTool.drawBoundingBox(shape);

        await expectLabelIsAssignedToDrawnShape(page, labelName);
    });

    test('Draw bounding box with selected label', async ({ page, boundingBoxTool }) => {
        await expectPreselectedLabelIsAssignedToDrawnShape(page, labelName, async () =>
            boundingBoxTool.drawBoundingBox(shape)
        );
    });

    test('Selects bounding box tool using hotkey', async ({ page, circleTool, boundingBoxTool }) => {
        // Change to circle tool first
        await circleTool.selectTool();

        await expect(page.getByRole('button', { name: 'Circle' })).toHaveAttribute('aria-pressed', 'true');

        await boundingBoxTool.selectTool();

        await expect(page.getByRole('button', { name: 'Bounding Box' })).toHaveAttribute('aria-pressed', 'true');
    });

    test('Undo and redo bounding box', async ({ page, boundingBoxTool, annotationListPage, undoRedo }) => {
        await annotationListPage.expectTotalAnnotationsToBe(0);

        await boundingBoxTool.drawBoundingBox(shape);

        const shapeLocator = getShapeLocator(page);

        await expectRectShape(shapeLocator, shape);

        await annotationListPage.expectTotalAnnotationsToBe(1);

        await undoRedo.undoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(1);
        await expectRectShape(shapeLocator, shape);

        await undoRedo.undoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(1);
        await expectRectShape(shapeLocator, shape);
    });

    test('Should use the correct cursor', async ({ page, boundingBoxTool }) => {
        await boundingBoxTool.selectTool();
        await page.mouse.move(100, 100);

        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('selection');
    });
});
