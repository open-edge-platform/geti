// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { Rect } from '../../../../src/core/annotations/shapes.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { project } from '../../../mocks/segmentation/mocks';
import { expectToBeEqualToPixelAccuracy } from '../../../utils/assertions';
import { clickAndMove, withRelative } from '../../../utils/mouse';
import {
    clearDefaultLabel,
    expectCircleShape,
    expectLabelIsAssignedToDrawnShape,
    expectPreselectedLabelIsAssignedToDrawnShape,
} from '../expect';
import { getCanvasCoordinates } from '../utils';

const getCircleShape = (page: Page) =>
    page.getByLabel('edit-annotations').getByLabel('Drag to move shape').locator('circle');

const getResizeAnchor = (page: Page) => page.getByLabel('Resize circle anchor');

const getResizeAnchorCoordinates = async (page: Page) => {
    const resizeAnchor = getResizeAnchor(page);

    const x = Number(await resizeAnchor.getAttribute('cx')) ?? 0;
    const y = Number(await resizeAnchor.getAttribute('cy')) ?? 0;

    return { x, y };
};

const expectResizeAnchorIsVisible = async (page: Page, canvasCoordinates: Omit<Rect, 'shapeType'>): Promise<void> => {
    const resizeAnchorCoordinates = await getResizeAnchorCoordinates(page);

    expect(resizeAnchorCoordinates.x).toBeGreaterThanOrEqual(canvasCoordinates.x);
    expect(resizeAnchorCoordinates.y).toBeGreaterThanOrEqual(canvasCoordinates.y);
    expect(resizeAnchorCoordinates.x).toBeLessThanOrEqual(canvasCoordinates.width);
    expect(resizeAnchorCoordinates.y).toBeLessThanOrEqual(canvasCoordinates.height);
};

test.describe('Circle', () => {
    const shape = { x: 300, y: 300, r: 100 };
    const labelName = 'horse';

    test.beforeEach(async ({ page, annotatorPath, circleTool, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.status(200), ctx.json(project)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.status(204)));

        await page.goto(annotatorPath);
        await circleTool.selectTool();
    });

    test('Draw circle', async ({ page, circleTool }) => {
        await circleTool.drawCircle(shape);

        const shapeLocator = getCircleShape(page);

        await expectCircleShape(shapeLocator, shape);
    });

    test('Translate circle', async ({ page, circleTool, selectionTool }) => {
        const newPoint = { x: shape.x + 100, y: shape.y + 100, r: 100 };
        await circleTool.drawCircle(shape);

        await selectionTool.selectTool();

        const relative = await withRelative(page);

        const startPoint = relative(shape.x, shape.y);
        const endPoint = relative(newPoint.x, newPoint.y);

        await clickAndMove(page, startPoint, endPoint);

        const shapeLocator = getCircleShape(page);

        await expectCircleShape(shapeLocator, newPoint);
    });

    test('Resize circle', async ({ page, circleTool, selectionTool }) => {
        await circleTool.drawCircle(shape);

        await selectionTool.selectTool();

        const { x, y } = await getResizeAnchorCoordinates(page);

        const relative = await withRelative(page);

        const moveX = 20;
        const anchorPoint = relative(x, y);
        const newEndPoint = relative(x + moveX, y);

        await clickAndMove(page, anchorPoint, newEndPoint);

        const shapeLocator = getCircleShape(page);

        await expectCircleShape(shapeLocator, { ...shape, r: shape.r + moveX });
    });

    test('Add label to circle', async ({ page, circleTool }) => {
        await clearDefaultLabel(page);

        await circleTool.drawCircle(shape);

        await expectLabelIsAssignedToDrawnShape(page, labelName);
    });

    test('Draw circle with selected label', async ({ page, circleTool }) => {
        await expectPreselectedLabelIsAssignedToDrawnShape(page, labelName, async () => circleTool.drawCircle(shape));
    });

    test('Should draw circle with changed radius', async ({ page, circleTool }) => {
        await circleTool.changeRadius(20);

        const radiusValue = await circleTool.getRadiusSliderValue();

        const circleShape = { ...shape, r: Number(radiusValue) };
        await circleTool.drawCircle(circleShape);

        await expectCircleShape(getCircleShape(page), circleShape);
    });

    test('Should draw circle with min radius', async ({ page, circleTool }) => {
        // select min radius
        await circleTool.changeRadius(-200);

        const radiusValue = await circleTool.getRadiusSliderValue();

        const circleShape = { ...shape, r: Number(radiusValue) };
        await circleTool.drawCircle(circleShape);

        await expectCircleShape(getCircleShape(page), circleShape);
    });

    test('Should draw circle with max radius', async ({ page, circleTool }) => {
        // select max radius
        await circleTool.changeRadius(800);

        const radiusValue = await circleTool.getRadiusSliderValue();

        const circleShape = { ...shape, r: Number(radiusValue) };
        await circleTool.drawCircle(circleShape);

        await expectCircleShape(getCircleShape(page), circleShape);
    });

    test('Drawing a circle with right click and not default radius sets a new radius value on slider', async ({
        page,
        circleTool,
    }) => {
        const newRadiusValue = Number(await circleTool.getRadiusSliderValue()) + 40;
        const circleShape = { ...shape, r: newRadiusValue };

        await circleTool.drawCircle({ ...circleShape, options: { button: 'right' } });

        await expectCircleShape(getCircleShape(page), circleShape);

        expectToBeEqualToPixelAccuracy(Number(await circleTool.getRadiusSliderValue()), newRadiusValue);
    });

    test('Dragging a whole circle outside the canvas removes the annotation (circle)', async ({
        page,
        circleTool,
        selectionTool,
    }) => {
        await circleTool.drawCircle(shape);

        await selectionTool.selectTool();

        const canvasCoordinates = await getCanvasCoordinates(page);
        const relative = await withRelative(page);

        const startPoint = relative(shape.x, shape.y);
        const endPointOutsideCanvas = relative(canvasCoordinates.width + shape.r, shape.y);

        await clickAndMove(page, startPoint, endPointOutsideCanvas);

        await expect(getCircleShape(page)).toBeHidden();
    });

    test('Show a circle radius preview while changing radius', async ({ page, circleTool }) => {
        const radiusSlider = await circleTool.getRadiusSlider();

        const radiusSliderBoundingBox = await radiusSlider.boundingBox();

        if (!radiusSliderBoundingBox) {
            throw new Error('Bounding box not found');
        }

        const { x, y, width, height } = radiusSliderBoundingBox;

        const startPoint = { x: x + width / 2, y: y + height / 2 };
        const endPoint = { x: startPoint.x + 20, y: startPoint.y / 2 };

        await page.mouse.move(startPoint.x, startPoint.y);
        await page.mouse.down();
        await page.mouse.move(endPoint.x, endPoint.y);

        const radiusValue = await circleTool.getRadiusSliderValue();

        const circlePreview = page.getByLabel('Circle size preview');
        const circleRadius = await circlePreview.getAttribute('r');

        await expect(circlePreview).toBeVisible();
        expect(radiusValue).toBe(circleRadius);

        await page.mouse.up();
    });

    test('Undo and redo circle', async ({ circleTool, page, undoRedo, annotationListPage }) => {
        await circleTool.drawCircle(shape);

        const shapeLocator = getCircleShape(page);

        await expectCircleShape(shapeLocator, shape);

        await annotationListPage.expectTotalAnnotationsToBe(1);

        await undoRedo.undoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(1);
        await expectCircleShape(shapeLocator, shape);

        await undoRedo.undoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(1);
        await expectCircleShape(shapeLocator, shape);
    });

    test('Should use the correct cursor', async ({ page, circleTool }) => {
        await circleTool.selectTool();
        await page.mouse.move(100, 100);

        expect(page.getByLabel('Circle tool canvas')).toBeTruthy();
    });

    test.describe('Circle resize anchor visibility', () => {
        const radius = 100;

        // The offset is used when drawing a circle near the border of the image,
        // the value is chosen so that we always start drawing inside of the canvas
        const offset = 30.0;

        test('Resize anchor is visible when circle is inside canvas', async ({ page, circleTool }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { width, height } = canvasCoordinates;

            const middleX = width / 2;
            const middleY = height / 2;

            await circleTool.drawCircle({ r: radius, x: middleX, y: middleY });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Resize anchor is visible when circle is partially outside of the canvas - top left corner', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { x, y } = canvasCoordinates;

            await circleTool.drawCircle({ x: x + offset, y: y + offset, r: radius });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Resize anchor is visible when circle is partially outside of the canvas - top middle', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { y, width } = canvasCoordinates;
            const middleX = width / 2;

            await circleTool.drawCircle({ x: middleX, y: y + offset, r: radius });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Resize anchor is visible when circle is partially outside of the canvas - top right corner', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { width, y } = canvasCoordinates;

            await circleTool.drawCircle({ r: radius, x: width - offset, y: y + offset });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Resize anchor is visible when circle is partially outside of the canvas - right middle', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { width, height } = canvasCoordinates;
            const middleY = height / 2;

            await circleTool.drawCircle({ r: radius, x: width - offset, y: middleY });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Resize anchor is visible when circle is partially outside of the canvas - right bottom corner', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { width, height } = canvasCoordinates;

            await circleTool.drawCircle({ r: radius, x: width - offset, y: height - offset });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Resize anchor is visible when circle is partially outside of the canvas - bottom middle', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { width, height } = canvasCoordinates;
            const middleX = width / 2;

            await circleTool.drawCircle({ r: radius, x: middleX, y: height - offset });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Resize anchor is visible when circle is partially outside of the canvas - bottom left corner', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { height, x } = canvasCoordinates;

            await circleTool.drawCircle({ r: radius, x: x + offset, y: height - offset });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Resize anchor is visible when circle is partially outside of the canvas - left middle', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { height, x } = canvasCoordinates;
            const middleY = height / 2;

            await circleTool.drawCircle({ r: radius, x: x + offset, y: middleY });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        // This test assumes that width of greater than height of the media
        test('Resize anchor is visible when circle is greater than height of the canvas', async ({
            page,
            circleTool,
        }) => {
            const canvasCoordinates = await getCanvasCoordinates(page);
            const { width, height } = canvasCoordinates;
            const middleY = height / 2;
            const middleX = width / 2;
            const newRadius = middleY + 50;

            await circleTool.drawCircle({ r: newRadius, x: middleX, y: middleY });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        // This test assumes that height is greater than width of the media
        test('Resize anchor is visible when circle is greater than width of the canvas', async ({
            page,
            circleTool,
        }) => {
            await circleTool.selectTool();

            const canvasCoordinates = await getCanvasCoordinates(page);
            const { width, height } = canvasCoordinates;
            const middleY = height / 2;
            const middleX = width / 2;
            const newRadius = middleX + 50;

            await circleTool.drawCircle({ r: newRadius, x: middleX, y: middleY });

            await expectResizeAnchorIsVisible(page, canvasCoordinates);
        });

        test('Selects circle tool using hotkey', async ({ page }) => {
            // Change to bounding box tool first
            await page.keyboard.press('b');

            await expect(page.getByRole('button', { name: 'Bounding Box' })).toHaveAttribute('aria-pressed', 'true');

            await page.keyboard.press('c');

            await expect(page.getByRole('button', { name: 'Circle' })).toHaveAttribute('aria-pressed', 'true');
        });
    });
});
