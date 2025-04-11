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

import { test } from '../../../fixtures/base-test';
import { VideoPlayerPage } from '../../../fixtures/page-objects/annotator/video-player-page';
import {
    activeSet,
    detectionAnnotations,
    detectionAnnotatorUrl,
    detectionChainProject,
    detectionProject,
    getMedia,
    getVideoMedia,
    noPredictionAnnotations,
} from './mocks';

function expectAnnotationShouldBeSelected(page: Page, annotationId: string) {
    return expect(page.getByTestId(`annotation-${annotationId}-thumbnailWrapper`)).toHaveClass(/isSelected/);
}

test.describe('Next / Previous / Submit', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetVideoDetail', (req, res, ctx) => {
            const id = String(req.params.video_id);
            const media = getVideoMedia(id);

            return res(ctx.json(media));
        });
        registerApiResponse('GetImageDetail', (req, res, ctx) => {
            const id = String(req.params.image_id);
            const media = getMedia(id);

            return res(ctx.json(media));
        });
    });
    test('Task chain', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionChainProject)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(detectionAnnotations)));
        registerApiResponse('FilterMedia', (_, res, ctx) =>
            res(
                ctx.json({
                    media: [getMedia('1'), getMedia('2'), getMedia('3'), getMedia('4')],
                    total_images: 4,
                    total_matched_images: 4,
                    total_matched_videos: 0,
                    total_matched_videos_frames: 0,
                    total_videos: 0,
                })
            )
        );

        registerApiResponse('GetActiveDataset', (_, res, ctx) =>
            res(
                ctx.json({
                    active_set: [activeSet.active_set[0], activeSet.active_set[2]],
                })
            )
        );

        await page.goto(`${detectionAnnotatorUrl}?task-id=${detectionChainProject.pipeline.tasks[3].id}`);

        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[1].id);
        await expect(page.getByLabel('Previous media item')).toBeDisabled();

        await page.getByLabel('Next media item').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[0].id);

        await page.getByLabel('Previous media item').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[1].id);

        await page.getByLabel('Submit annotations').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[1].id);

        await page.getByLabel('Next media item').click();
        await expect(() => expect(page.url()).toContain('image/2')).toPass();

        await page.getByLabel('Previous media item').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[1].id);

        await page.getByRole('button', { name: /choose annotation dataset/i }).click();
        await page.getByRole('option', { name: 'Active set' }).click();

        await page.getByLabel('Next media item').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[0].id);

        await page.getByLabel('Previous media item').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[1].id);

        await page.getByLabel('Submit annotations').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[1].id);

        await page.getByLabel('Next media item').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[0].id);

        await page.getByLabel('Previous media item').click();
        await expectAnnotationShouldBeSelected(page, detectionAnnotations.annotations[1].id);

        await page.getByLabel('Next media item').click();
        await page.getByLabel('Submit annotations').click();

        await expect(() => expect(page.url()).toContain('image/4')).toPass();
    });

    test.describe('Single task', () => {
        test.beforeEach(async ({ registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionProject)));

            registerApiResponse('FilterMedia', (_, res, ctx) =>
                res(
                    ctx.json({
                        media: [getMedia('1'), getMedia('2'), getVideoMedia('3'), getMedia('4')],
                        total_images: 3,
                        total_matched_images: 3,
                        total_matched_videos: 1,
                        total_matched_videos_frames: 300,
                        total_videos: 1,
                    })
                )
            );

            registerApiResponse('GetActiveDataset', (_, res, ctx) => res(ctx.json(activeSet)));

            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(
                    ctx.json({
                        ...detectionAnnotations,
                        media_identifier: { frame_index: 0, type: 'video_frame', video_id: '3' },
                        annotations: [],
                    })
                )
            );

            registerApiResponse('GetVideoFrameAnnotation', (_, res, ctx) =>
                res(
                    ctx.json({
                        ...detectionAnnotations,
                        media_identifier: { frame_index: 0, type: 'video_frame', video_id: '3' },
                        annotations: [],
                    })
                )
            );

            registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions: [] })));
            registerApiResponse('GetVideoFramePrediction', (_, res, ctx) => res(ctx.json(noPredictionAnnotations)));
        });

        test('Images / Videos', async ({ page }) => {
            await page.goto(detectionAnnotatorUrl);

            const videoPlayer = new VideoPlayerPage(page);

            await page.getByLabel('Next media item').click();
            await expect(() => expect(page.url()).toContain('image/2')).toPass();

            await page.getByLabel('Previous media item').click();
            await expect(() => expect(page.url()).toContain('image/1')).toPass();

            await page.getByLabel('Submit annotations').click();
            await expect(() => expect(page.url()).toContain('image/2')).toPass();

            await page.getByLabel('Next media item').click();

            await expect(() => expect(page.url()).toContain('video/3')).toPass();

            await videoPlayer.expectFrameNumberToBeSelected(0);
            await page.getByLabel('Next media item').click();
            await videoPlayer.expectFrameNumberToBeSelected(30);

            await page.getByLabel('Previous media item').click();
            await videoPlayer.expectFrameNumberToBeSelected(0);

            await page.getByLabel('Submit annotations').click();
            await videoPlayer.expectFrameNumberToBeSelected(30);

            await page.getByLabel('Next media item').click();
            await expect(() => expect(page.url()).toContain('image/4')).toPass();

            await page.getByLabel('Previous media item').click();
            await expect(() => expect(page.url()).toContain('video/3')).toPass();

            await page.getByRole('button', { name: /choose annotation dataset/i }).click();
            await page.getByRole('option', { name: 'Active set' }).click();

            await page.getByLabel('Next media item').click();

            await videoPlayer.expectFrameNumberToBeSelected(30);

            await page.getByLabel('Previous media item').click();
            await videoPlayer.expectFrameNumberToBeSelected(30);

            await page.getByLabel('Submit annotations').click();
            await videoPlayer.expectFrameNumberToBeSelected(60);
        });

        test('Active set video next', async ({ page }) => {
            await page.goto(`${detectionAnnotatorUrl}?active=true`);

            await page.getByLabel('Next media item').click();
            await expect(() => expect(page.url()).toContain('video/3')).toPass();
        });

        test('Active set', async ({ page }) => {
            await page.goto(`${detectionAnnotatorUrl}?active=true`);

            await page.getByLabel('Submit annotations').click();
            await expect(() => expect(page.url()).toContain('video/3')).toPass();

            await page.getByLabel('Next media item').click();
            await page.getByLabel('Next media item').click();

            await expect(() => expect(page.url()).toContain('image/4')).toPass();

            await page.getByLabel('Previous media item').click();
            await expect(() => expect(page.url()).toContain('video/3')).toPass();
        });
    });
});
