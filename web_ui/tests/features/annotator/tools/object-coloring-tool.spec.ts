// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { Point, Rect } from '../../../../src/core/annotations/shapes.interface';
import { delay } from '../../../../src/shared/utils';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { ObjectColoringToolPage } from '../../../fixtures/page-objects/annotator/object-coloring-tool-page';
import { media, project } from '../../../mocks/segmentation/mocks';
import { registerFullImage } from '../../../utils/api';
import { resolveTestAssetPath } from '../../../utils/dataset';
import { getAnnotationListItems, getSubmitButton } from '../../../utils/selectors';
import { getLine, getPolylineArea } from '../utils';

const waitForWatershedResponse = async (page: Page) => {
    await expect(page.getByLabel('accept watershed annotation')).toBeEnabled();
};

const getLabelName = (page: Page, n: number) =>
    page.locator(`[aria-label="Label shortcuts"] > div > div > :nth-child(${n}) span`).innerText();

const getPolygonPoint = async (page: Page, n: number): Promise<Array<Point>> => {
    const polygonLocator = page.locator(`#annotations-canvas-tools  polygon:nth-child(${n})`);
    const points = (await polygonLocator.getAttribute('points')) || '';

    return points.split(' ').map((point) => ({ x: +point.split(',')[0], y: +point.split(',')[1] }));
};

const BRUSH_SIZES = [
    { sliderPoint: 525, value: 8 },
    { sliderPoint: 535, value: 15 },
    { sliderPoint: 587, value: 53 },
];

const isFitPolygon = (polygon: Array<Point>, expectedBox: Omit<Rect, 'shapeType'>): boolean =>
    polygon.every(
        (point) =>
            point.x >= expectedBox.x &&
            point.x <= expectedBox.x + expectedBox.width &&
            point.y >= expectedBox.y &&
            point.y <= expectedBox.y + expectedBox.height
    );

const expectNewAnnotationsToHaveLabels = async (page: Page, labels: string[]) => {
    const annotationListItems = await getAnnotationListItems(page);

    expect(await annotationListItems.count()).toBe(labels.length);

    await Promise.all(
        labels.map(async (label, index) => {
            return await expect(annotationListItems.nth(labels.length - 1 - index)).toContainText(label);
        })
    );
};

const changeLabelToBackgroundAndDrawShape = async (
    page: Page,
    objectColoringTool: ObjectColoringToolPage,
    shape: { points: { x: number; y: number }[] }
) => {
    // Change label to background and draw background shape
    await page.getByRole('button', { name: 'label Select label' }).click();
    await page.locator('div[role="group"] >> #option-Background-color').click();

    await objectColoringTool.drawPolyline(shape);

    await waitForWatershedResponse(page);
};

const shapes = {
    background: {
        points: [
            { x: 300, y: 550 },
            { x: 250, y: 200 },
            { x: 680, y: 60 },
            { x: 810, y: 60 },
            { x: 700, y: 400 },
            { x: 630, y: 420 },
            { x: 585, y: 570 },
            { x: 520, y: 450 },
            { x: 470, y: 400 },
            { x: 390, y: 450 },
            { x: 350, y: 580 },
        ],
    },
    0: {
        points: [
            { x: 340, y: 450 },
            { x: 400, y: 300 },
            { x: 550, y: 300 },
            { x: 570, y: 450 },
            { x: 590, y: 300 },
            { x: 660, y: 300 },
            { x: 700, y: 230 },
        ],
    },
    1: {
        points: [
            { x: 155, y: 180 },
            { x: 185, y: 160 },
        ],
    },
    2: {
        points: [
            { x: 920, y: 215 },
            { x: 920, y: 280 },
        ],
    },
};

const shape = {
    points: [
        { x: 300 + 33, y: 33 },
        { x: 300 + 33, y: 330 },
        { x: 300 + 330, y: 330 },
    ],
};

const backgroundShape = {
    points: [
        { x: 300 + 330, y: 33 },
        { x: 300 + 330, y: 330 },
        { x: 300 + 330, y: 333 },
    ],
};

test.beforeEach(async ({ page, annotatorPath, objectColoringTool, registerApiResponse }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.status(200), ctx.json(project)));
    registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));
    registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.status(204)));

    await page.goto(annotatorPath);
    await objectColoringTool.selectTool();
});

test.describe('Object coloring', () => {
    test('Draw and accept annotation', async ({ page, objectColoringTool }) => {
        const firstLabelName = await getLabelName(page, 1);

        await objectColoringTool.drawPolyline(shape);
        await expect(getSubmitButton(page)).toBeDisabled();

        await changeLabelToBackgroundAndDrawShape(page, objectColoringTool, backgroundShape);

        await page
            .locator('#annotations-canvas-tools >> polygon[fill-opacity="var(--annotation-fill-opacity)"]')
            .isVisible();

        await objectColoringTool.acceptAnnotation();

        await expect(getSubmitButton(page)).toBeEnabled();
        await expectNewAnnotationsToHaveLabels(page, [firstLabelName]);
    });

    test('Draw and accept many times', async ({ page, objectColoringTool }) => {
        await objectColoringTool.drawPolyline(shape);
        await expect(getSubmitButton(page)).toBeDisabled();

        await changeLabelToBackgroundAndDrawShape(page, objectColoringTool, backgroundShape);

        await page
            .locator('#annotations-canvas-tools >> polygon[fill-opacity="var(--annotation-fill-opacity)"]')
            .isVisible();

        await objectColoringTool.acceptAnnotation();

        expect(await page.getByRole('list', { name: 'Annotations list' }).getByText('horse').count()).toBe(1);
    });

    test('Draw shape and check tool works correctly', async ({ page, objectColoringTool }) => {
        const boundingBox = {
            x: 265,
            y: 100,
            width: 495,
            height: 450,
        };

        await objectColoringTool.drawPolyline(shapes[0]);

        await changeLabelToBackgroundAndDrawShape(page, objectColoringTool, shapes.background);

        await page
            .locator('#annotations-canvas-tools >> polygon[fill-opacity="var(--annotation-fill-opacity)"]')
            .isVisible();

        // Check that the tool works correctly
        const polygonPoints = await getPolygonPoint(page, 1);
        expect(isFitPolygon(polygonPoints, boundingBox)).toBe(true);
    });

    test('Draws and rejects annotation', async ({ page, objectColoringTool }) => {
        await objectColoringTool.drawPolyline(shape);

        await changeLabelToBackgroundAndDrawShape(page, objectColoringTool, backgroundShape);

        await page
            .locator('#annotations-canvas-tools >> polygon[fill-opacity="var(--annotation-fill-opacity)"]')
            .isVisible();

        await objectColoringTool.rejectAnnotation();

        await expect(getAnnotationListItems(page)).toHaveCount(0);
        await expect(getSubmitButton(page)).toBeEnabled();
    });

    test('Draw multiple shapes', async ({ page, objectColoringTool }) => {
        const labelNames = await Promise.all([1, 2, 3].map(async (index) => await getLabelName(page, index)));

        await objectColoringTool.drawPolyline(shapes[0]);

        await changeLabelToBackgroundAndDrawShape(page, objectColoringTool, shapes.background);

        // Change label to the second one and draw shape
        await page.getByRole('button', { name: 'label Select label' }).click();
        await page.getByRole('group').locator(`#option-${labelNames[1]}-color`).click();
        await objectColoringTool.drawPolyline(shapes[1]);
        await waitForWatershedResponse(page);

        // Change label to the third one and draw shape
        await page.getByRole('button', { name: 'label Select label' }).click();
        await page.getByRole('group').locator(`#option-${labelNames[2]}-color`).click();
        await objectColoringTool.drawPolyline(shapes[2]);
        await waitForWatershedResponse(page);

        await objectColoringTool.acceptAnnotation();

        await expect(getSubmitButton(page)).toBeEnabled();
        await expectNewAnnotationsToHaveLabels(page, labelNames);
    });

    test('Selects object coloring tool using hotkey', async ({ page }) => {
        // Change to circle tool first
        await page.keyboard.press('c');

        await expect(page.getByRole('button', { name: 'Circle' })).toHaveAttribute('aria-pressed', 'true');

        await page.keyboard.press('w');

        await expect(page.getByRole('button', { name: 'Object coloring' })).toHaveAttribute('aria-pressed', 'true');
    });

    // test_object_coloring_undo_redo_before_accept_annotation
    // test_object_coloring_undo_redo_after_accept_annotation
    test('Undo/redo works correctly before/after accepting annotations', async ({ page, objectColoringTool }) => {
        await objectColoringTool.drawPolyline(shape);
        await expect(getSubmitButton(page)).toBeDisabled();

        await changeLabelToBackgroundAndDrawShape(page, objectColoringTool, backgroundShape);

        await waitForWatershedResponse(page);

        await page
            .locator('#annotations-canvas-tools >> polygon[fill-opacity="var(--annotation-fill-opacity)"]')
            .isVisible();

        // Undo
        await page.getByLabel('undo').click();

        await page
            .locator('#annotations-canvas-tools >> polygon[fill-opacity="var(--annotation-fill-opacity)"]')
            .isHidden();

        await expect(page.getByRole('button', { name: 'accept watershed annotation' })).toBeDisabled();

        // Redo and accept
        await page.getByLabel('redo').click();
        await objectColoringTool.acceptAnnotation();

        // Undo
        await page.getByLabel('undo').click();

        await expect(getAnnotationListItems(page)).toHaveCount(0);
    });

    test('Change brush size', async ({ page, objectColoringTool }) => {
        const LINE_START_X = 330;
        const LINE_LENGTH = 300;
        const LINES_Y_PLACEMENT = [33, 150, 230];

        await objectColoringTool.drawPolyline(getLine(LINE_START_X, LINES_Y_PLACEMENT[0], LINE_LENGTH));
        await objectColoringTool.changeBrushSize(BRUSH_SIZES[0].sliderPoint, BRUSH_SIZES[1].sliderPoint);

        await objectColoringTool.drawPolyline(getLine(LINE_START_X, LINES_Y_PLACEMENT[1], LINE_LENGTH));

        await objectColoringTool.changeBrushSize(BRUSH_SIZES[1].sliderPoint, BRUSH_SIZES[2].sliderPoint);
        await objectColoringTool.drawPolyline(getLine(LINE_START_X, LINES_Y_PLACEMENT[2], LINE_LENGTH));

        const polylines = page.locator('polyline');
        await expect(polylines.nth(0)).toHaveAttribute('stroke-width', `${BRUSH_SIZES[0].value * 2}`);
        await expect(polylines.nth(1)).toHaveAttribute('stroke-width', `${BRUSH_SIZES[1].value * 2}`);
        await expect(polylines.nth(2)).toHaveAttribute('stroke-width', `${BRUSH_SIZES[2].value * 2}`);
    });

    test('Show brush size preview while size is changing', async ({ page, objectColoringTool }) => {
        await objectColoringTool.openBrushSlider();

        await page.mouse.move(BRUSH_SIZES[0].sliderPoint, objectColoringTool.BRUSH_SIZE_SLIDER_Y);
        await page.mouse.down();
        await page.mouse.move(BRUSH_SIZES[1].sliderPoint, BRUSH_SIZES[2].sliderPoint);

        const brushSizePreview = page.getByLabel('Circle size preview');
        const brushSizePreviewValue = await brushSizePreview.getAttribute('r');

        await expect(brushSizePreview).toBeVisible();

        await expect(page.getByLabel('Brush size slider').getByRole('slider')).toHaveValue(brushSizePreviewValue ?? '');

        await page.mouse.up();
    });

    test('Marker should have the same size like brush size', async ({ page, objectColoringTool }) => {
        await objectColoringTool.changeBrushSize(BRUSH_SIZES[0].sliderPoint, BRUSH_SIZES[1].sliderPoint);

        const sliderValue = page.getByLabel('Brush size slider').locator('input[type=range]');
        const markerValue = (await page.getByLabel('Marker').getAttribute('r')) ?? '';

        await expect(sliderValue).toHaveValue(markerValue);
    });

    test('Annotation accuracy should be reflected upon sensitivity change', async ({
        page,
        objectColoringTool,
        registerApiResponse,
    }) => {
        registerApiResponse('GetImageDetail', (_, res, ctx) =>
            res(
                ctx.json({
                    ...media,
                    media_information: {
                        display_url:
                            '/v2/projects/60d3549a3e6080a926e5ef12/media/images/613a23866674c43ae7a777aa/display/full',
                        height: 3456,
                        width: 4608,
                    },
                })
            )
        );
        registerFullImage(registerApiResponse, resolveTestAssetPath('spade-ace.webp'));

        const horizontalLine = {
            points: [
                { x: 1660, y: 2000 },
                { x: 1700, y: 2070 },
            ],
        };
        const backgroundOne = {
            points: [
                { x: 700, y: 1300 },
                { x: 700, y: 1800 },
            ],
        };

        const backgroundTwo = {
            points: [
                { x: 3000, y: 1280 },
                { x: 3000, y: 1360 },
                { x: 3060, y: 1460 },
                { x: 3160, y: 1460 },
            ],
        };

        await page.reload();

        await objectColoringTool.selectTool();

        await objectColoringTool.drawPolyline(horizontalLine);
        await expect(getSubmitButton(page)).toBeDisabled();

        await changeLabelToBackgroundAndDrawShape(page, objectColoringTool, backgroundOne);

        await objectColoringTool.drawPolyline(backgroundTwo);

        await page
            .locator('#annotations-canvas-tools >> polygon[fill-opacity="var(--annotation-fill-opacity)"]')
            .first()
            .isVisible();

        // Calculate resulting area
        // Get polygon and calculate its area
        const initialPolygon = page.locator('polygon');
        const initialPolygonArea = await getPolylineArea(initialPolygon);

        // Change sensitivity and select the middle of the slider
        await page.getByLabel('Sensitivity button').click();
        await page.getByLabel('Sensitivity slider').click({ position: { x: 55, y: 0 } });

        await delay(2000);

        // Verify that the area of the resulting polyline is different than the original
        const finalPolygon = page.locator('polygon');
        const finalPolygonArea = await getPolylineArea(finalPolygon);

        expect(finalPolygonArea).not.toBe(initialPolygonArea);
    });

    test('Undo and redo object coloring', async ({ page, objectColoringTool, undoRedo, annotationListPage }) => {
        const firstLabelName = await getLabelName(page, 1);

        await objectColoringTool.drawPolyline(shape);

        await changeLabelToBackgroundAndDrawShape(page, objectColoringTool, backgroundShape);

        await objectColoringTool.acceptAnnotation();

        await expectNewAnnotationsToHaveLabels(page, [firstLabelName]);

        await undoRedo.undoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(1);

        await undoRedo.undoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(1);
        await expectNewAnnotationsToHaveLabels(page, [firstLabelName]);
    });

    test('Should use the correct cursor', async ({ page, objectColoringTool }) => {
        await objectColoringTool.selectTool();
        await page.mouse.move(100, 100);

        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('cursor: none');
    });
});
