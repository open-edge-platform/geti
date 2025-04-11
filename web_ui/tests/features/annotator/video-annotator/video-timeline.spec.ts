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

import { expect, Page } from '@playwright/test';

import { Rect } from '../../../../src/core/annotations/shapes.interface';
import { test } from '../../../fixtures/base-test';
import { VideoPlayerPage } from '../../../fixtures/page-objects/annotator/video-player-page';
import { clickAndMove, withRelative } from '../../../utils/mouse';
import {
    annotatorUrl,
    FIXED_DTO_SHAPE,
    mockVideoAnnotations,
    mockVideoPredictions,
    MODEL_SOURCE,
    project,
    USER_SOURCE,
    userAnnotationsResponse,
    VIDEO_PAGINATION_PROPERTIES,
    videoMediaItem,
} from './mocks';

const drawBoundingBox = async (page: Page, { x, y, width, height }: Omit<Rect, 'shapeType'>) => {
    const relative = await withRelative(page);
    const startPoint = relative(x, y);
    const endPoint = relative(x + width, y + height);

    await clickAndMove(page, startPoint, endPoint);
};

const addAnAnnotation = async (page: Page) => {
    await page.getByRole('button', { name: 'Bounding Box' }).click();

    await drawBoundingBox(page, { x: 10, y: 10, width: 100, height: 100 });
};

test.describe('Video annotator', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetVideoDetail', (_, res, ctx) => res(ctx.json(videoMediaItem)));

        registerApiResponse('CreateVideoFrameAnnotation', async (req, res, ctx) => {
            return res(
                ctx.json({
                    annotation_state_per_task: [],
                    annotations: req.body.annotations.map((annotation) => ({
                        ...annotation,
                        labels: annotation.labels.map((label) => ({
                            ...label,
                            source: { user_id: 'user@test.com' },
                        })),
                    })),
                })
            );
        });

        registerApiResponse('GetVideoAnnotation', (_req, res, ctx) => {
            const video_annotations = [60, 240].map((frameIndex) => {
                const label = frameIndex > 180 ? 'GoldFish' : 'YellowFish';

                return mockVideoAnnotations(frameIndex, label);
            });

            return res(
                ctx.json({
                    video_annotation_properties: VIDEO_PAGINATION_PROPERTIES,
                    video_annotations,
                })
            );
        });

        registerApiResponse('GetBatchPrediction', (_req, res, ctx) => {
            return res(
                ctx.json({
                    batch_predictions: [60, 180, 240].map((frameIndex) => {
                        const label = frameIndex > 180 ? 'GoldFish' : 'YellowFish';

                        const { annotations: predictions } = mockVideoPredictions(frameIndex, label);
                        return {
                            predictions,
                            created: '2021-09-08T12:43:22.290000+00:00',
                            media_identifier: {
                                video_id: '61387685df33ae8280c33d9d',
                                type: 'video_frame',
                                frame_index: frameIndex,
                            },
                        };
                    }),
                })
            );
        });
    });

    test('Timeline', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => {
            return res(ctx.json({ predictions: [] }));
        });

        registerApiResponse('GetVideoFrameAnnotation', (req, res, ctx) => {
            if (req.params.frame_index === '60') {
                const frameIndex = 60;
                const label = 'YellowFish';

                return res(ctx.json(mockVideoAnnotations(frameIndex, label)));
            }

            return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
        });

        await page.goto(annotatorUrl);

        const videoPlayerPage = new VideoPlayerPage(page);

        const timeline = videoPlayerPage.timeline();
        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        await timeline.expectFrameMode('1/1');

        await timeline.expectColCount(60);
        await timeline.expectRowCount(8);

        await timeline.expectUserLabel(60, 'Fish');
        await timeline.expectPredictedLabel(60, 'Fish');

        await timeline.expectUserLabel(60, 'Yellow Fish');
        await timeline.expectPredictedLabel(60, 'Yellow Fish');

        // Making the frameskip 60 times smaller should make it so that we show 60 times more columns

        await timeline.toggleFrameMode();

        // Move mouse from the frame mode button
        await page.mouse.move(100, 100);

        await timeline.expectFrameMode('ALL');
        await timeline.expectColCount(60 * 60);
    });

    test('it updates the video timeline when submitting annotations', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetVideoFrameAnnotation', (_, res, ctx) => {
            return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
        });

        registerApiResponse('GetSinglePrediction', (_, res, ctx) => {
            return res(ctx.json({ predictions: [] }));
        });

        registerApiResponse('GetVideoAnnotation', (_, res, ctx) => {
            return res(
                ctx.json({
                    video_annotation_properties: VIDEO_PAGINATION_PROPERTIES,
                    video_annotations: [],
                })
            );
        });

        registerApiResponse('GetBatchPrediction', (_, res, ctx) => {
            return res(ctx.json({ batch_predictions: [] }));
        });

        await page.goto(annotatorUrl);

        // Create an arbitrary annotation with a Fish label
        await addAnAnnotation(page);

        const videoPlayerPage = new VideoPlayerPage(page);
        const timeline = videoPlayerPage.timeline();

        await timeline.expectUserLabel(0, 'Fish', 'No label');

        // Submit the annotation and verify that we now show a fish in the timeline
        await page.getByRole('button', { name: /Submit annotations/i }).click();
        await timeline.expectUserLabel(0, 'Fish');
    });

    test('it updates the video timeline when getting new annotations or predictions', async ({
        page,
        registerApiResponse,
    }) => {
        const annotations = [
            {
                id: `annotation-1`,
                shape: FIXED_DTO_SHAPE,
                labels: [
                    {
                        id: '63283aedc80c9c686fd3b1f1',
                        name: 'Fish',
                        color: '#cc94daff',
                        probability: 1.0,
                        source: USER_SOURCE,
                    },
                    {
                        id: 'ClownFish',
                        name: 'ClownFish',
                        color: '#cc94daff',
                        probability: 1.0,
                        source: USER_SOURCE,
                    },
                ],
                labels_to_revisit: [],
            },
        ];

        registerApiResponse('GetVideoFrameAnnotation', (req, res, ctx) => {
            if (req.params.frame_index !== '120') {
                return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
            }
            return res(ctx.json({ ...userAnnotationsResponse, annotations }));
        });

        registerApiResponse('GetSinglePrediction', (_req, res, ctx) => {
            const predictions = [
                {
                    id: `prediction-annotation-1`,
                    shape: FIXED_DTO_SHAPE,
                    labels: [
                        {
                            id: '63283aedc80c9c686fd3b1f1',
                            name: 'Fish',
                            color: '#cc94daff',
                            probability: 0.33,
                            source: MODEL_SOURCE,
                        },
                        {
                            id: 'ClownFish',
                            name: 'ClownFish',
                            color: '#cc94daff',
                            probability: 0.33,
                            source: MODEL_SOURCE,
                        },
                    ],
                    labels_to_revisit: [],
                },
            ];

            return res(ctx.json({ predictions }));
        });

        registerApiResponse('GetVideoAnnotation', (_, res, ctx) => {
            return res(
                ctx.json({
                    video_annotation_properties: VIDEO_PAGINATION_PROPERTIES,
                    video_annotations: [],
                })
            );
        });

        await page.goto(annotatorUrl);

        const videoPlayerPage = new VideoPlayerPage(page);
        const timeline = videoPlayerPage.timeline();

        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        await timeline.expectUserLabel(120, 'Fish', 'No label');

        await test.step('updating timeline when navigating', async () => {
            await videoPlayerPage.goToFrame(120);
            await videoPlayerPage.expectFrameNumberToBeSelected(120);

            await timeline.expectPredictedLabel(120, 'Fish');
            await timeline.expectPredictedLabel(120, 'Clownfish');

            await timeline.expectUserLabel(120, 'Fish');
            await timeline.expectUserLabel(120, 'Clownfish');
        });
    });

    test('Allows the user to continue annotating when batch infernece fails', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetBatchPrediction', async (_, res, ctx) => {
            return res(ctx.status(503));
        });

        await page.goto(annotatorUrl);

        const videoPlayerPage = new VideoPlayerPage(page);
        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        // We fail to load any batch predictions, after which the loading
        // indicator should be replaced by "No prediction"
        const timeline = videoPlayerPage.timeline();
        await timeline.expectNoPredictedLabel(120, 'Fish');

        await expect(page.getByRole('heading', { name: 'We are experiencing technical difficulties' })).toBeHidden();
    });
});
