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

import { expect } from '@playwright/test';

import { test } from '../../../../fixtures/base-test';
import { labelIDs } from '../../../../mocks/anomaly/anomaly-classification/mocks';
import { expectToBeEqualToPixelAccuracy } from '../../../../utils/assertions';
import { VideoRangePage } from '../../utils';
import { project, videoAnnotations, videoMediaItem } from './mocks';

const datasetUrl =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/6290a8f9003ddb3967f14385/datasets/639757d00d117eb552d21300';

test.describe('Anomaly classification video ranges', () => {
    let videoRanges: Array<{ start_frame: number; end_frame: number; label_ids: string[] }>;
    let videoRangesUpdated: boolean;
    test.beforeEach(async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('FilterMedia', (_, res, ctx) =>
            res(
                ctx.json({
                    media: [videoMediaItem],
                    total_images: 0,
                    total_matched_images: 0,
                    total_matched_videos: 1,
                    total_matched_videos_frames: 901,
                    total_videos: 1,
                })
            )
        );

        registerApiResponse('GetVideoAnnotationRange', (_, res, ctx) =>
            res(ctx.json({ range_labels: [{ start_frame: 0, end_frame: 900, label_ids: [labelIDs.normal] }] }))
        );

        registerApiResponse('GetVideoDetail', (_, res, ctx) => res(ctx.json(videoMediaItem)));

        registerApiResponse('GetVideoAnnotation', (_, res, ctx) => res(ctx.json(videoAnnotations)));
        registerApiResponse('CreateVideoAnnotationRange', (req, res, ctx) => {
            videoRangesUpdated = true;
            videoRanges = req.body.range_labels;

            return res(ctx.json({}));
        });

        await page.goto(datasetUrl);
        await page.locator('[class*=gridItem]').first().hover();
        await page.getByLabel('open menu').first().click();

        const anomalyVideoRangePage = new VideoRangePage(page);

        await anomalyVideoRangePage.openVideoRangeDialog();

        await expect(anomalyVideoRangePage.videoRangeDialog).toBeVisible();
        await expect(anomalyVideoRangePage.getVideoRangeDialogHeader()).toBeVisible();

        videoRangesUpdated = false;
    });

    test('Video ranges', async ({ page }) => {
        const anomalyVideoRangePage = new VideoRangePage(page);

        await anomalyVideoRangePage.createRange(50, 200, 'Anomalous');
        await anomalyVideoRangePage.createRange(300, 400, 'Anomalous');

        await anomalyVideoRangePage.createRange(350, 450, 'Normal');

        await anomalyVideoRangePage.changeLabel('Anomalous');

        await anomalyVideoRangePage.saveRanges();

        await expect(anomalyVideoRangePage.videoRangeDialog).toBeHidden();

        expect(videoRangesUpdated).toBe(true);

        expect(videoRanges).toEqual([
            { start_frame: 0, end_frame: 121, label_ids: [labelIDs.anomalous] },
            { start_frame: 122, end_frame: 182, label_ids: [labelIDs.normal] },
            { start_frame: 183, end_frame: 214, label_ids: [labelIDs.anomalous] },
            { start_frame: 215, end_frame: 900, label_ids: [labelIDs.normal] },
        ]);
    });

    test('should extend the previous range', async ({ page }) => {
        const anomalyVideoRangePage = new VideoRangePage(page);

        await anomalyVideoRangePage.createRange(0, 200, 'Anomalous');
        await anomalyVideoRangePage.createRange(200, 400, 'Anomalous');

        await expect(anomalyVideoRangePage.getRanges()).toHaveCount(2);
    });

    test('should not be able to move video thumb outside the video range', async ({ page }) => {
        const anomalyVideoRangePage = new VideoRangePage(page);

        const start = 20;
        await anomalyVideoRangePage.selectRange(start, 200);

        // Simulate moving slider
        for (let i = start; i < 230; i += 15) {
            await anomalyVideoRangePage.moveVideoSliderThumb(i);
        }

        const videoThumbBoxAtTheEndEdge = await anomalyVideoRangePage.getVideoThumbBox();
        const videoThumbXAtTheEndEdge = videoThumbBoxAtTheEndEdge.x + videoThumbBoxAtTheEndEdge.width / 2;
        const endRangeThumbBox = await anomalyVideoRangePage.getEndRangeThumbBox();

        expectToBeEqualToPixelAccuracy(videoThumbXAtTheEndEdge, endRangeThumbBox.x);

        // Simulate moving slider
        for (let i = 230; i > 0; i -= 15) {
            await anomalyVideoRangePage.moveVideoSliderThumb(i);
        }

        const videoThumbBoxAtTheStartEdge = await anomalyVideoRangePage.getVideoThumbBox();
        const videoThumbXAtTheStartEdge = videoThumbBoxAtTheStartEdge.x + videoThumbBoxAtTheStartEdge.width / 2;
        const startRangeThumbBox = await anomalyVideoRangePage.getStartRangeThumbBox();
        const startRangeThumbX = startRangeThumbBox.x + startRangeThumbBox.width;

        expectToBeEqualToPixelAccuracy(videoThumbXAtTheStartEdge, startRangeThumbX);
    });

    test('toggling off and on the range selector should reset the ranges', async ({ page }) => {
        const anomalyVideoRangePage = new VideoRangePage(page);

        await expect(anomalyVideoRangePage.getAddRangeArea()).toBeHidden();

        await anomalyVideoRangePage.selectRange(0, 200);

        await expect(anomalyVideoRangePage.getAddRangeArea()).toBeVisible();

        await anomalyVideoRangePage.toggleRangeSelector();
        await anomalyVideoRangePage.toggleRangeSelector();

        await expect(anomalyVideoRangePage.getAddRangeArea()).toBeHidden();
    });
});
