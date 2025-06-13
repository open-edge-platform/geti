// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { expect, Page } from '@playwright/test';

import { Point, Rect } from '../../../../src/core/annotations/shapes.interface';
import { ShapeType } from '../../../../src/core/annotations/shapetype.enum';
import { isShapeWithinRoi } from '../../../../src/pages/annotator/tools/utils';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { OpenApiFixtures } from '../../../fixtures/open-api';
import { annotatorUrl, userAnnotationsResponse } from '../../../mocks/classification/mocks';
import * as detectionOrientedMocks from '../../../mocks/detection-oriented/mocks';
import { media, project } from '../../../mocks/segmentation/mocks';
import { withRelative } from '../../../utils/mouse';
import { getPolylineArea } from '../utils';
import { project as detectionSegmentationProject } from './../../../mocks/detection-segmentation/mocks';

const getDynamicBoundingBox = (page: Page) => page.locator('svg rect[role="application"]');
const getResultingShape = (page: Page) => page.locator('svg').getByLabel('result shape');
const getUndoButtonLocator = (page: Page) => page.getByLabel('undo');
const getRedoButtonLocator = (page: Page) => page.getByLabel('redo');
const getDynamicSelectionModeSwitch = (page: Page) => page.getByRole('switch', { name: 'Dynamic selection mode' });
const getRightClickModeSwitch = (page: Page) => page.getByRole('switch', { name: 'Right-click mode' });

const clickInsideCanvas = async (page: Page, point: Point, options?: { button?: 'left' | 'right' | 'middle' }) => {
    const relative = await withRelative(page);
    const relativePoint = relative(point.x, point.y);

    await page.mouse.click(relativePoint.x, relativePoint.y, options);
};

const waitForRITMtoProcess = async (page: Page, variant: string, index: number) => {
    await expect(page.getByTestId(`point-${variant}-${index}`)).toBeVisible();
};

const setupDetectionSegmentation = async (page: Page, registerApiResponse: OpenApiFixtures['registerApiResponse']) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionSegmentationProject)));

    const detectionTask = detectionSegmentationProject.pipeline.tasks[1];
    const detectionLabels = detectionTask.labels;
    const segmentationTask = detectionSegmentationProject.pipeline.tasks[3];
    const segmentationLabels = segmentationTask.labels;

    if (detectionLabels === undefined || segmentationLabels === undefined) {
        throw new Error('Invalid task input for test, please fix the fixture');
    }

    const annotations = [
        {
            id: '7f641911-5dec-4965-9774-5e4d8de42ecd',
            labels: [
                {
                    ...detectionLabels[0],
                    probability: 1,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
            labels_to_revisit: [],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', x: 120, y: 118, width: 89, height: 101 },
        },
        {
            id: 'cd399888-ab0b-4816-9dfe-07d8a60a435d',
            labels: [
                {
                    ...segmentationLabels[0],
                    probability: 1,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
            labels_to_revisit: [],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', x: 150, y: 130, width: 20, height: 20 },
        },
        {
            id: '0fb04c9b-9ea0-4549-9e24-91c7c61d97bc',
            labels: [
                {
                    ...detectionLabels[0],
                    probability: 1,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
            labels_to_revisit: [],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', x: 873, y: 172, width: 66, height: 204 },
        },
        {
            id: 'cd399888-ab0b-4816-9dfe-07d8a60a435e',
            labels: [
                {
                    ...segmentationLabels[0],
                    probability: 1,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
            labels_to_revisit: [],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', x: 875, y: 175, width: 20, height: 100 },
        },
        {
            id: 'cd399888-ab0b-4816-9dfe-07d8a60a435b',
            labels: [
                {
                    ...detectionLabels[0],
                    probability: 1,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
            labels_to_revisit: [],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { x: 257, y: 100, width: 511, height: 443, type: 'RECTANGLE' },
        },
        {
            id: 'cd399888-ab0b-4816-9dfe-07d8a60a435c',
            labels: [
                {
                    ...segmentationLabels[0],
                    probability: 1,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
            labels_to_revisit: [],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: { type: 'RECTANGLE', x: 300, y: 200, width: 100, height: 100 },
        },
    ];

    registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
        res(ctx.json({ ...userAnnotationsResponse, annotations }))
    );

    const url = paths.project.annotator.image({
        organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
        workspaceId: '61011e42d891c82e13ec92da',
        projectId: '61012cdb1d38a5e71ef3baf9',
        datasetId: '635fce72fc03e87df9becd14',
        imageId: '613a23866674c43ae7a777aa',
    });
    await page.goto(`${url}?task-id=${segmentationTask.id}`);

    return annotations;
};

test.describe('Interactive segmentation tool', () => {
    test.beforeEach(({ registerApiExample, registerApiResponse }) => {
        registerApiExample('GetAllWorkspaces', '');
        registerApiExample('GetProjectStatus', 'Waiting for classification annotations');
        registerApiExample('GetServerStatus', 'Server status response');
        registerApiExample('SetSettings', 'Successfully set response');

        registerApiExample('FilterMedia', 'Combined media list response');
        registerApiExample('GetActiveDataset', 'Combined media list response');

        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
        );
    });

    test('adds and subtracts annotations with a single click', async ({ page, interactiveSegmentationTool }) => {
        await page.goto(annotatorUrl, { timeout: 10000 });

        await interactiveSegmentationTool.selectTool();

        // Add 2 positive points with left click
        await clickInsideCanvas(page, { x: 392, y: 258 });

        // Get polyline and calculate its area
        const initialPolyline = getResultingShape(page);
        const initialPolylineArea = await getPolylineArea(initialPolyline);

        // Left click on the generated polyline produces negative point
        await clickInsideCanvas(page, { x: 361, y: 305 });
        await waitForRITMtoProcess(page, 'negative', 1);

        // Verify that the area of the resulting polyline is smaller than the original
        const finalPolyline = getResultingShape(page);
        const finalPolylineArea = await getPolylineArea(finalPolyline);

        expect(finalPolylineArea).toBeLessThan(initialPolylineArea);
    });

    test('subtracts a polyline with the right click if Right-click mode is active', async ({
        page,
        interactiveSegmentationTool,
    }) => {
        await page.goto(annotatorUrl);

        await interactiveSegmentationTool.selectTool();

        // Add a positive point with left click
        await clickInsideCanvas(page, { x: 392, y: 258 });
        await waitForRITMtoProcess(page, 'positive', 0);

        // Get polyline and calculate its area
        const initialPolyline = getResultingShape(page);
        const initialPolylineArea = await getPolylineArea(initialPolyline);

        // Enable subtract mode
        await getRightClickModeSwitch(page).click();

        // Left click on the previously generated polyline
        await clickInsideCanvas(page, { x: 392, y: 258 + 10 }, { button: 'right' });
        await waitForRITMtoProcess(page, 'negative', 1);

        // Verify that the area of the resulting polyline is smaller than the original
        const finalPolyline = getResultingShape(page);
        const finalPolylineArea = await getPolylineArea(finalPolyline);

        expect(finalPolylineArea).toBeLessThan(initialPolylineArea);
    });

    test('undo redo works properly', async ({ page, interactiveSegmentationTool, undoRedo }) => {
        await page.goto(annotatorUrl);

        await interactiveSegmentationTool.selectTool();

        // Add a positive point with left click
        await clickInsideCanvas(page, { x: 392, y: 258 });
        await waitForRITMtoProcess(page, 'positive', 0);

        await expect(getResultingShape(page)).toBeVisible();

        // Undo annotation
        await undoRedo.undoUsingButton();

        await expect(getResultingShape(page)).toBeHidden();

        // Redo annotation
        await undoRedo.redoUsingButton();

        await expect(getResultingShape(page)).toBeVisible();

        // Undo annotation
        await undoRedo.undoUsingShortcut();

        await expect(getResultingShape(page)).toBeHidden();

        // Redo annotation
        await undoRedo.redoUsingShortcut();

        await expect(getResultingShape(page)).toBeVisible();
    });

    test('It should zoom out when properly in the segmentation sub task', async ({
        page,
        interactiveSegmentationTool,
        registerApiResponse,
    }) => {
        const annotations = await setupDetectionSegmentation(page, registerApiResponse);

        const grid = page.getByTestId('annotation-list-thumbnail-grid');
        const input = grid.getByRole('img', { name: `Annotation ${annotations[4].id}` });
        await expect(input).toHaveAttribute('aria-current', 'true');

        await interactiveSegmentationTool.selectTool();

        // Add a positive point with left click
        await clickInsideCanvas(page, { x: 392, y: 258 });
        await waitForRITMtoProcess(page, 'positive', 0);

        // Check that the input is still selected
        await expect(input).toHaveAttribute('aria-current', 'true');
    });

    test('Selects RITM tool using hotkey', async ({ page, interactiveSegmentationTool }) => {
        await page.goto(annotatorUrl);

        await interactiveSegmentationTool.selectTool();

        // Change to circle tool first
        await page.keyboard.press('c');

        await expect(page.getByRole('button', { name: 'Circle' })).toHaveAttribute('aria-pressed', 'true');

        await page.keyboard.press('i');

        await expect(page.getByRole('button', { name: 'Interactive segmentation' })).toHaveAttribute(
            'aria-pressed',
            'true'
        );
    });

    test('Should use the correct cursor', async ({ page, interactiveSegmentationTool }) => {
        await page.goto(annotatorUrl);

        await interactiveSegmentationTool.selectTool();
        await page.mouse.move(100, 100);

        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('pencil-plus');

        await clickInsideCanvas(page, { x: 392, y: 258 });
        await expect(page.getByTestId('point-positive-0')).toBeVisible();

        expect(await page.getByLabel('result shape').getAttribute('cursor')).toContain('pencil-minus');
    });

    test('Should display the correct tooltips', async ({ page, interactiveSegmentationTool }) => {
        await page.goto(annotatorUrl);

        await interactiveSegmentationTool.selectTool();

        const rightClickModeButton = page.getByLabel('Right-click mode');
        await rightClickModeButton.hover();

        await expect(
            page.getByText(
                'With this mode ON press left-click to place positive points and right-click to ' +
                    'place negative points.'
            )
        ).toBeVisible();
    });
});

test.describe('with disabled dynamic selection mode', () => {
    const shape: Rect = { x: 500, y: 500, width: 200, height: 200, shapeType: ShapeType.Rect };
    const shapeOne: Rect = { x: 500, y: 500, width: 200, height: 200, shapeType: ShapeType.Rect };
    const shapeTwo: Rect = { x: 100, y: 100, width: 100, height: 100, shapeType: ShapeType.Rect };

    test.beforeEach(async ({ page, annotatorPath, interactiveSegmentationTool, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.status(200), ctx.json(project)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.status(204)));

        await page.goto(annotatorPath);

        await interactiveSegmentationTool.selectTool();
    });

    test('creates an annotation inside a custom bounding box', async ({ page, interactiveSegmentationTool }) => {
        // Disable dynamic selection mode
        await getDynamicSelectionModeSwitch(page).click();

        // Draw a custom bounding box
        await interactiveSegmentationTool.drawBoundingBox(shape);

        // Click inside the dynamic box
        await clickInsideCanvas(page, { x: shape.x + 50, y: shape.y + 50 });

        await waitForRITMtoProcess(page, 'positive', 0);

        // Get the polyline and extract all its points
        const resultingPolyline = getResultingShape(page);
        const polylineHTMLPoints = await resultingPolyline.getAttribute('points');

        const polylinePoints: Point[] =
            polylineHTMLPoints?.split(' ').map((point) => {
                const [x, y] = point.split(',');

                return { x: Number(x), y: Number(y) };
            }) || [];

        // Check if polyline is within the customBoundingBox
        expect(
            isShapeWithinRoi(shape, {
                points: polylinePoints,
                shapeType: ShapeType.Polygon,
            })
        ).toBeTruthy();
    });

    test('undo redo works properly when dynamic mode is disabled', async ({
        page,
        selectionTool,
        interactiveSegmentationTool,
    }) => {
        // Disable dynamic selection mode
        await getDynamicSelectionModeSwitch(page).click();

        // Draw a custom bounding box
        await interactiveSegmentationTool.drawBoundingBox(shapeOne);

        await getDynamicBoundingBox(page).boundingBox();

        // Click inside the dynamic box
        await clickInsideCanvas(page, { x: shapeOne.x + 40, y: shapeOne.y + 40 });

        await waitForRITMtoProcess(page, 'positive', 0);

        // Accept annotation
        await interactiveSegmentationTool.acceptAnnotation();

        // Draw another custom bounding box
        await interactiveSegmentationTool.drawBoundingBox(shapeTwo);

        await getDynamicBoundingBox(page).boundingBox();

        // Click inside the dynamic box
        await clickInsideCanvas(page, { x: shapeTwo.x + 40, y: shapeTwo.y + 40 });

        await waitForRITMtoProcess(page, 'positive', 0);

        // Accept annotation
        await interactiveSegmentationTool.acceptAnnotation();

        await selectionTool.selectTool();

        // Deselect annotation
        await clickInsideCanvas(page, { x: 10, y: 10 });

        await expect(page.getByLabel('annotations').getByLabel(/Not selected shape/i)).toHaveCount(2);

        // Undo annotation
        await getUndoButtonLocator(page).click();

        await expect(
            page.getByLabel('edit-annotations').getByLabel('Drag to move shape').locator('polygon')
        ).toHaveCount(1);

        // Redo annotation
        await getRedoButtonLocator(page).click();

        await expect(
            page.getByLabel('edit-annotations').getByLabel('Drag to move shape').locator('polygon')
        ).toHaveCount(1);

        await expect(page.getByLabel('annotations').getByLabel(/Not selected shape/i)).toHaveCount(1);
    });

    test('Enter / ESC should work for Interactive Segmentation confirmation / cancelling', async ({
        page,
        interactiveSegmentationTool,
        annotationListPage,
    }) => {
        // Click inside the dynamic box
        await clickInsideCanvas(page, { x: shapeOne.x, y: shapeOne.y });

        await waitForRITMtoProcess(page, 'positive', 0);

        await interactiveSegmentationTool.acceptAnnotation(true);
        await annotationListPage.expectTotalAnnotationsToBe(1);

        // Click inside the dynamic box
        await clickInsideCanvas(page, { x: shapeTwo.x + 50, y: shapeTwo.y + 50 });

        await waitForRITMtoProcess(page, 'positive', 0);

        await interactiveSegmentationTool.cancelAnnotation(true);
        await annotationListPage.expectTotalAnnotationsToBe(1);
    });
});

test.describe('Rotated bounding box', () => {
    test.beforeEach(async ({ registerApiResponse, page, annotatorPage }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionOrientedMocks.project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionOrientedMocks.media)));

        await page.goto(detectionOrientedMocks.annotatorUrl, { timeout: 15000 });
        await annotatorPage.deleteAllAnnotations();
    });

    test('Rotated bounding boxes can be created with interactive segmentation tool', async ({
        page,
        interactiveSegmentationTool,
        annotationListPage,
    }) => {
        await interactiveSegmentationTool.selectTool();

        // Add 2 positive points with left click
        await clickInsideCanvas(page, { x: 400, y: 330 });

        await waitForRITMtoProcess(page, 'positive', 0);
        await interactiveSegmentationTool.acceptAnnotation(true);
        await annotationListPage.expectTotalAnnotationsToBe(1);
    });
});
