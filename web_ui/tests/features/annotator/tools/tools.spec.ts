// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { annotatorUrl, media, project } from '../../../mocks/segmentation/mocks';
import { waitForLoadingToBeFinished } from '../../../utils/assertions';
import { zoomInImage } from '../../../utils/mouse';
import { VIEWPORT_TYPE } from '../../../utils/test-type';
import { getZoomLevel } from '../../../utils/zoom';

test.describe('Image viewing area maximizing', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
    });

    test('Switching drawing tools should not reset the zoom level', async ({ page }) => {
        /* test_image_viewing_area_maximize */
        /*
         * 1-select the box drawing tool.
         * 2-zoom in the selected image.
         * 3-select the selection tool.
         * 4-select the polygon drawing tool.
         * the zoom level should not change
         * */

        await page.goto(annotatorUrl);
        await waitForLoadingToBeFinished(page);

        await page.getByRole('button', { name: 'Bounding Box' }).click();

        await zoomInImage(page, { x: 150, y: 150 }, -400);
        const zoomLevel = await getZoomLevel(page);

        await page.getByRole('button', { name: 'Selection', exact: true }).click();
        await page.getByRole('button', { name: 'Polygon', exact: true }).click();

        expect(await getZoomLevel(page)).toBe(zoomLevel);
    });

    test(`${VIEWPORT_TYPE.MOBILE} Check if toolbar is not too wide 
    (normally and after zooming) on small viewport`, async ({ page }) => {
        /* test_image_viewing_area_maximize */
        /*
         * 1. As a user upload a dataset.
         * 2. Selects one image and maximizes viewing area.
         * 3. Verify that all annotation tools can be still used.
         * 4. Minimize viewing area, verify that all page elements visible.
         * */

        await page.goto(annotatorUrl);
        await waitForLoadingToBeFinished(page);
        const annotatorToolbar = page.locator('#annotator-toolbar');

        await expect(annotatorToolbar).toBeVisible();

        await zoomInImage(page, { x: 150, y: 150 }, -24000);

        await expect(annotatorToolbar).toBeVisible();

        await expect(async () => {
            const annotatorToolbarBoxAfterZoom = await annotatorToolbar.boundingBox();

            expect(await annotatorToolbar.boundingBox()).toStrictEqual(annotatorToolbarBoxAfterZoom);
            expect(annotatorToolbarBoxAfterZoom?.width).toBe(48);
        }).toPass();
    });
});
