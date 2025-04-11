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

import * as fs from 'fs';
import * as path from 'path';

import { Page } from '@playwright/test';

import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { expect } from '../../../fixtures/base-test';
import { VideoPlayerPage } from '../../../fixtures/page-objects/annotator/video-player-page';
import { selectShape, translateShape } from '../utils';
import { annotatorUrl, frameAnnotations, project, userAnnotationsResponse, videoMediaItem } from './mocks';

const expectConfirmationDialogToBeShown = async (page: Page) => {
    await expect(page.getByRole('dialog')).toBeVisible();
};

const clickCancel = async (page: Page) => {
    const button = page.getByRole('button', { name: /Cancel/i });

    await button.click();
};

test.describe('Video annotator', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(videoMediaItem)));
        registerApiResponse('GetVideoDetail', (_, res, ctx) => res(ctx.json(videoMediaItem)));

        registerApiResponse('GetVideoFrameAnnotation', (_, res, ctx) => {
            return res(ctx.json({ ...userAnnotationsResponse, annotations: frameAnnotations }));
        });
    });

    test('Video navigation', async ({ page }) => {
        await page.goto(annotatorUrl);

        const videoPlayerPage = new VideoPlayerPage(page);

        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        await videoPlayerPage.goToFrame(120);
        await videoPlayerPage.expectFrameNumberToBeSelected(120);

        await videoPlayerPage.goToFrame(3000);
        await videoPlayerPage.expectFrameNumberToBeSelected(3000);

        await videoPlayerPage.goToFrame(0);
        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        // NOTE: This line fixes the issue when in tests we want to click next button but thumbnail is visible
        await page.mouse.move(100, 100);

        // Next 0 -> 60
        await videoPlayerPage.next();
        await videoPlayerPage.expectFrameNumberToBeSelected(60);

        // Next 60 -> 120
        await videoPlayerPage.next();
        await videoPlayerPage.expectFrameNumberToBeSelected(120);

        // Previous 120 -> 60
        await videoPlayerPage.previous();
        await videoPlayerPage.expectFrameNumberToBeSelected(60);
    });

    test('Video navigation using keyboard shortcuts', async ({ page }) => {
        await page.goto(annotatorUrl);

        const videoPlayerPage = new VideoPlayerPage(page);
        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        // Next 0 -> 60
        await videoPlayerPage.nextFrameUsingKeyboardShortcut();
        await videoPlayerPage.expectFrameNumberToBeSelected(60);

        // Next 60 -> 120
        await videoPlayerPage.nextFrameUsingKeyboardShortcut();
        await videoPlayerPage.expectFrameNumberToBeSelected(120);

        // Previous 120 -> 60
        await videoPlayerPage.previousFrameUsingKeyboardShortcut();
        await videoPlayerPage.expectFrameNumberToBeSelected(60);

        // Previous 60 -> 0
        await videoPlayerPage.previousFrameUsingKeyboardShortcut();
        await videoPlayerPage.expectFrameNumberToBeSelected(0);
    });

    test('Confirmation dialog is shown when user has unsaved changes', async ({ page, selectionTool }) => {
        // Select the next frame so that we can use the previous button
        await page.goto(`${annotatorUrl.slice(0, -2)}/60`);

        const videoPlayerPage = new VideoPlayerPage(page);

        await videoPlayerPage.expectFrameNumberToBeSelected(60);

        // Edit an existing annotation
        await selectionTool.selectTool();
        await selectShape(page, frameAnnotations[0].shape);
        await translateShape(page, frameAnnotations[0].shape, { x: 300, y: 150 });

        await videoPlayerPage.goToFrame(60);

        await expectConfirmationDialogToBeShown(page);
        await clickCancel(page);

        await videoPlayerPage.next();
        await expectConfirmationDialogToBeShown(page);
        await clickCancel(page);

        await videoPlayerPage.previous();
        await expectConfirmationDialogToBeShown(page);
        await clickCancel(page);

        const playButton = videoPlayerPage.getPlayButton();
        if (await playButton.isEnabled()) {
            await videoPlayerPage.play();
            await expectConfirmationDialogToBeShown(page);
            await clickCancel(page);
        }
    });

    test.describe('Streaming video player', () => {
        test('Playing a video', async ({ page, registerApiResponse, browserName }) => {
            const videoPath = path.resolve(
                __dirname,
                browserName === 'chromium'
                    ? '../../../datasets/cartoon-fish/fish_60.webm'
                    : '../../../datasets/cartoon-fish/fish_60.mp4'
            );

            test.skip(!fs.existsSync(videoPath), 'this test requires you to setup a local dataset, see #4890');

            const videoBuffer = fs.readFileSync(videoPath);

            registerApiResponse('DownloadVideoStream', async (_req, res, ctx) => {
                const contentType = browserName === 'chromium' ? 'video/webm' : 'video/mp4';

                return res(
                    ctx.set('Content-Length', videoBuffer.byteLength.toString()),
                    ctx.set('Content-Type', contentType),
                    // @ts-expect-error our OpenAPI types can't correctly handle binary responses
                    ctx.body(videoBuffer)
                );
            });

            await page.goto(annotatorUrl);

            const videoPlayerPage = new VideoPlayerPage(page);

            await videoPlayerPage.closeVideoTimeline();
            await videoPlayerPage.expectFrameNumberToBeSelected(0);

            // Play, wait 1 second, so 0 -> 60 (the video has 60 fps)
            await videoPlayerPage.play();

            await videoPlayerPage.expectFrameNumberToBeSelected(60);
        });

        test('Disables video player when the video is not supported', async ({ page, registerApiResponse }) => {
            registerApiResponse('DownloadVideoStream', async (_req, res, ctx) => {
                return res(ctx.status(404));
            });

            await page.goto(annotatorUrl);

            const videoPlayerPage = new VideoPlayerPage(page);
            await videoPlayerPage.expectFrameNumberToBeSelected(0);

            const playButton = videoPlayerPage.getPlayButton();
            await expect(playButton).toBeDisabled();
        });

        test('Allows muting the volume', async ({ page }) => {
            await page.goto(annotatorUrl);

            const videoPlayerPage = new VideoPlayerPage(page);
            await videoPlayerPage.expectFrameNumberToBeSelected(0);

            const playButton = videoPlayerPage.getPlayButton();
            await expect(playButton).toBeDisabled();

            const unmuteButton = videoPlayerPage.getUnMuteButton();
            await expect(unmuteButton).toBeVisible();
            await unmuteButton.click();

            const muteButton = videoPlayerPage.getMuteButton();
            await expect(muteButton).toBeVisible();
            await muteButton.click();
        });
    });
});
