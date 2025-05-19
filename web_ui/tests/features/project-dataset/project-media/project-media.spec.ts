// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';
import { range } from 'lodash-es';
import { v4 as uuidv4 } from 'uuid';

import { OpenApiResponseBody } from '../../../../src/core/server/types';
import { paths } from '../../../../src/core/services/routes';
import { ViewModes } from '../../../../src/shared/components/media-view-modes/utils';
import { delay } from '../../../../src/shared/utils';
import { test } from '../../../fixtures/base-test';
import { waitForLoadingToBeFinished } from '../../../utils/assertions';
import { resolveAntelopePath } from '../../../utils/dataset';
import { getMedia } from '../../annotator/navigation/mocks';

const url = paths.project.dataset.media({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: '61011e42d891c82e13ec92da',
    projectId: 'project-id',
    datasetId: 'dataset-id',
});

test('Filter media', async ({ page, mediaPage }) => {
    await page.goto(url);
    const bucket = await mediaPage.getBucket();

    // Apply filters
    const filterDialog = await bucket.openFilterDialog();
    await filterDialog.setAnnotationStatusFilter('Unannotated');
    await filterDialog.addNewFilter();
    await filterDialog.setMediaNameFilter('Test');
    await filterDialog.close();

    // Remove filters
    const filterButtons = page.getByRole('button', { name: /remove-rule/i });
    const rules = await filterButtons.count();
    for (let idx = rules; idx > 0; idx--) {
        await filterButtons.nth(idx - 1).click();
    }
});

test('Media view modes', async ({ page, mediaPage }) => {
    await page.goto(url);

    const bucket = await mediaPage.getBucket();

    await bucket.changeViewMode(ViewModes.DETAILS);

    await bucket.changeViewMode(ViewModes.SMALL);
    await bucket.changeViewMode(ViewModes.MEDIUM);
    await bucket.changeViewMode(ViewModes.LARGE);
});

test('Hovering img shows media details tooltip', async ({ openApi, page }) => {
    await page.goto(url);

    const { mock } = openApi.mockResponseForOperation('FilterMedia');
    const { media } = mock;
    const mediaId = media[0].id;

    const image = page.locator(`#grid-media-item-image-${mediaId} img`);

    await page.mouse.move(0, 0);
    await image.hover();

    await expect(page.locator(`#media-item-tooltip-${mediaId}`)).toBeVisible();
});

test('Media upload', async ({ page, mediaPage, registerApiResponse, openApi }) => {
    const uploads: OpenApiResponseBody<'UploadImage'>[] = [];

    registerApiResponse('UploadImage', async (_, res, ctx) => {
        const { mock, status } = openApi.mockResponseForOperation('UploadImage');
        const media = { ...mock, id: uuidv4(), name: `Antelope ${uploads.length}` };
        uploads.push(media);

        return res(ctx.status(status), ctx.json(media));
    });

    registerApiResponse('FilterMedia', (_, res, ctx) => {
        return res(
            ctx.json({
                media: uploads,
                total_matched_images: uploads.length,
                total_matched_videos: 0,
                total_matched_video_frames: 0,
                total_images: uploads.length,
                total_videos: 0,
            }),
            ctx.status(200)
        );
    });

    registerApiResponse('DeleteAnImage', (_, res, ctx) => {
        uploads.pop();

        return res(ctx.status(200));
    });

    await page.goto(url);

    const files = range(1, 4).map((_) => resolveAntelopePath());
    const bucket = await mediaPage.getBucket();
    await bucket.uploadFiles(files);

    // Select image
    await bucket.selectImage('Antelope 0');
    await bucket.expectTotalMedia({ images: 3 });
    await expect(page.getByText('3 images')).toBeVisible();
    await expect(page.getByText('Selected: 1')).toBeVisible();

    // Delete image
    await bucket.deleteSelectedImages();
    await expect(page.getByText('2 images')).toBeVisible();
});

const getFilterMediaResponse = (totalImages: number) => {
    return {
        media: Array.from({ length: totalImages }).map((__, index) => getMedia(`${index}`)),
        total_images: totalImages,
        total_matched_images: 0,
        total_matched_videos: 0,
        total_matched_videos_frames: 0,
        total_videos: 0,
    };
};

test('Download image', async ({ page, registerApiResponse }) => {
    const totalImages = 3;
    const mediaDelay = 1000;

    registerApiResponse('FilterMedia', async (_, res, ctx) => {
        await delay(mediaDelay);

        return res(ctx.json(getFilterMediaResponse(totalImages)));
    });

    await page.goto(url);

    await waitForLoadingToBeFinished(page);

    const image = page.locator('#grid-media-item-image-0');
    await expect(image).toBeVisible();
    await image.hover();
    await page.getByRole('button', { name: 'open menu' }).click();
    await page.getByRole('menuitem', { name: 'Download' }).click();

    const [download] = await Promise.all([
        page.waitForEvent('download'),
        page.getByRole('menuitem', { name: 'Download' }).click(),
    ]);

    expect(await download.failure()).toBeNull();
});
