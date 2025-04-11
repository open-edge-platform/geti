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

import { expect, Page } from '@playwright/test';

import { annotatorTest as test } from '../../fixtures/annotator-test';
import { annotatorUrl, project } from '../../mocks/segmentation/mocks';
import { withRelative, zoomInImage } from '../../utils/mouse';

const getShapeLocator = (page: Page) =>
    page.getByLabel('edit-annotations').getByLabel('Drag to move shape').locator('g');

// The screen.mouse.dblclick requires us to set a slowMo value of at least 100
test.use({ launchOptions: { slowMo: 100 } });

test.describe('Annotator', () => {
    test.beforeEach(async ({ registerApiResponse, page, annotatorPage, boundingBoxTool }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));

        await page.goto(annotatorUrl);
        await annotatorPage.deleteAllAnnotations();
        await boundingBoxTool.selectTool();
    });

    // test_annotations_labels_color
    test('Annotation fill color should match the label selected from the default label combobox', async ({
        boundingBoxTool,
        page,
    }) => {
        const shape = { x: 10, y: 20, width: 300, height: 300 };

        // Select 'donkey' label from default label combobox
        const combobox = page.getByRole('textbox', {
            name: /select default label/i,
        });

        await combobox.focus();

        await page
            .getByRole('listitem', {
                name: new RegExp('label item donkey'),
            })
            .click();

        // Draw shape
        await boundingBoxTool.drawBoundingBox(shape);

        const shapeLocator = getShapeLocator(page);

        await expect(shapeLocator).toHaveAttribute('fill', '#00ffffff');
    });

    // test_annotate_after_undo
    test('Undo/redo should work properly with annotations', async ({ boundingBoxTool, page, annotationListPage }) => {
        const shapeOne = { x: 10, y: 20, width: 300, height: 300 };
        const shapeTwo = { x: 50, y: 30, width: 100, height: 300 };
        const shapeThree = { x: 25, y: 90, width: 90, height: 20 };
        const undoButton = page.getByLabel('undo');
        const redoButton = page.getByLabel('redo');

        // Select 'donkey' label from default label combobox
        const combobox = page.getByRole('textbox', {
            name: /select default label/i,
        });

        await combobox.focus();

        await page
            .getByRole('listitem', {
                name: new RegExp('label item donkey'),
            })
            .click();

        // Select bounding box (to also blur from the label search)
        await page.getByRole('button', { name: /^Bounding Box$/ }).click();

        // Draw shape
        await boundingBoxTool.drawBoundingBox(shapeOne);

        await annotationListPage.expectTotalAnnotationsToBe(1);

        // Undo
        await undoButton.click();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        // Add 2 more shapes
        await boundingBoxTool.drawBoundingBox(shapeTwo);
        await boundingBoxTool.drawBoundingBox(shapeThree);

        await annotationListPage.expectTotalAnnotationsToBe(2);

        // Undo
        await undoButton.click();

        await annotationListPage.expectTotalAnnotationsToBe(1);

        // Redo
        await redoButton.click();

        await annotationListPage.expectTotalAnnotationsToBe(2);
    });

    // test_annotations_fit_image_to_screen
    test('Fit image to screen works properly', async ({ page }) => {
        const INIT_ZOOM = 1.28;
        const ZOOM_AFTER_SCROLL = 1.48;
        const initialZoom = Number(await page.getByLabel('Zoom level').getAttribute('data-value'));

        // Note: Initial zoom depends on the image quality,
        // and for this image that we use in the mocks the initial is 128%
        expect(initialZoom).toBeCloseTo(INIT_ZOOM);

        // Zoom in
        await zoomInImage(page, { x: 150, y: 150 }, -200);

        expect(Number(await page.getByLabel('Zoom level').getAttribute('data-value'))).toBeCloseTo(ZOOM_AFTER_SCROLL);

        // Fit to screen
        await page.getByRole('button', { name: 'Fit image to screen' }).click();

        await expect(async () => {
            expect(Number(await page.getByLabel('Zoom level').getAttribute('data-value'))).toBeCloseTo(INIT_ZOOM);
        }).toPass();

        // Zoom in again
        await zoomInImage(page, { x: 150, y: 150 }, -200);

        await expect(async () => {
            expect(Number(await page.getByLabel('Zoom level').getAttribute('data-value'))).toBeCloseTo(
                ZOOM_AFTER_SCROLL
            );
        }).toPass();

        // Press 'fit to screen' hotkey
        await page.keyboard.press('Control+f');

        await expect(async () => {
            expect(Number(await page.getByLabel('Zoom level').getAttribute('data-value'))).toBeCloseTo(INIT_ZOOM);
        }).toPass();
    });

    test('Check zooming the image and returning to default size by double click', async ({ page }) => {
        // test_canvas_zoom
        // 1. zoom in canvas using mouse scroll wheel.
        // 2. double-click on canvas to return to original size
        // 3. zoom out canvas using mouse scroll wheel.
        // 4. double-click on canvas to return to original size

        const noValuesRect = {
            x: 0,
            y: 0,
            width: 0,
            height: 0,
        };

        // Zoom in
        const relative = await withRelative(page);
        const point = relative(150, 150);

        await page.keyboard.press('Control+f');

        await page.mouse.move(point.x, point.y);

        const baseRect = (await page.locator('id=annotations-canvas-tools').boundingBox()) ?? noValuesRect;

        await page.mouse.wheel(0, -300);
        const zoomedInRect = (await page.locator('id=annotations-canvas-tools').boundingBox()) ?? noValuesRect;
        expect(baseRect?.width < zoomedInRect?.width).toBeTruthy();
        expect(baseRect?.height < zoomedInRect?.height).toBeTruthy();

        await page.mouse.dblclick(point.x, point.y);

        await expect(async () => {
            const returnedToDefaultRect =
                (await page.locator('id=annotations-canvas-tools').boundingBox()) ?? noValuesRect;
            expect(baseRect.width).toBeCloseTo(returnedToDefaultRect.width);
            expect(baseRect.height).toBeCloseTo(returnedToDefaultRect.height);
        }).toPass({ timeout: 1000 });

        await page.mouse.wheel(0, 300);
        const zoomedOutRect = (await page.locator('id=annotations-canvas-tools').boundingBox()) ?? noValuesRect;
        expect(baseRect?.width > zoomedOutRect?.width).toBeTruthy();
        expect(baseRect?.height > zoomedOutRect?.height).toBeTruthy();
        await page.mouse.dblclick(point.x, point.y);

        await expect(async () => {
            const returnedToDefaultRect2 =
                (await page.locator('id=annotations-canvas-tools').boundingBox()) ?? noValuesRect;

            expect(baseRect.width).toBeCloseTo(returnedToDefaultRect2.width);
            expect(baseRect.height).toBeCloseTo(returnedToDefaultRect2.height);
        }).toPass({ timeout: 1000 });
    });
});
