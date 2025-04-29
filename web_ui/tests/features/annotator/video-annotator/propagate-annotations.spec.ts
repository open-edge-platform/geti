// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { AnnotationDTO, SHAPE_TYPE_DTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { annotatorTest } from '../../../fixtures/annotator-test';
import { VideoPlayerPage } from '../../../fixtures/page-objects/annotator/video-player-page';
import { expectToBeEqualToPixelAccuracy } from '../../../utils/assertions';
import { selectShape, translateShape } from '../utils';
import { annotatorUrl, frameAnnotations, project, userAnnotationsResponse, videoMediaItem } from './mocks';

// This helper fixture allows us to set the annotations for the 0th and 60th frame,
// while also keeping track of any changes to these annotations
const test = annotatorTest.extend<{
    registerAnnotationsPerFrame: (
        initial?: Record<number, AnnotationDTO[]>
    ) => Promise<Record<number, AnnotationDTO[]>>;
}>({
    registerAnnotationsPerFrame: async ({ registerApiResponse, page }, use) => {
        await use(async (frameToAnnotations = { 0: frameAnnotations, 60: [] }) => {
            registerApiResponse('CreateVideoFrameAnnotation', async (req, res, ctx) => {
                frameToAnnotations[Number(req.params.frame_index)] = req.body.annotations as AnnotationDTO[];
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

            registerApiResponse('GetVideoFrameAnnotation', (req, res, ctx) => {
                if (!req.params.video_id) {
                    return res(ctx.json(userAnnotationsResponse));
                }

                const frameIndex = Number(req.params.frame_index);
                const annotations = frameToAnnotations[frameIndex];
                return res(ctx.json({ ...userAnnotationsResponse, annotations }));
            });

            await page.goto(annotatorUrl);

            return frameToAnnotations;
        });
    },
});

test.describe('Propagate annotations', () => {
    test.beforeEach(({ registerApiResponse }) => {
        // Important to project test
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(videoMediaItem)));
        registerApiResponse('GetVideoDetail', (_, res, ctx) => res(ctx.json(videoMediaItem)));
    });

    test('copies annotations from the current frame to the next', async ({ page, registerAnnotationsPerFrame }) => {
        const frameToAnnotations = await registerAnnotationsPerFrame();

        const videoPlayerPage = new VideoPlayerPage(page);

        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        await videoPlayerPage.propagateAnnotations();
        await videoPlayerPage.expectFrameNumberToBeSelected(60);

        frameAnnotations.forEach((annotation, index) => {
            expect(frameToAnnotations[60][index].id).toEqual(annotation.id);
        });
    });

    test('it submits changes', async ({ page, registerAnnotationsPerFrame, selectionTool }) => {
        const frameToAnnotations = await registerAnnotationsPerFrame();

        const videoPlayerPage = new VideoPlayerPage(page);

        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        // Edit an existing annotation
        await selectionTool.selectTool();
        await selectShape(page, frameAnnotations[0].shape);
        await translateShape(page, frameAnnotations[0].shape, { x: 300, y: 150 });

        // Propagate annotations
        await videoPlayerPage.propagateAnnotations();
        await videoPlayerPage.expectFrameNumberToBeSelected(60);

        // Expect annotations to have been submitted in both the origianl frame and the next frame
        expect(frameToAnnotations[0]).toHaveLength(1);
        expect(frameToAnnotations[60]).toHaveLength(1);
        expect(frameToAnnotations[0][0].id).toEqual(frameAnnotations[0].id);
        expect(frameToAnnotations[60][0].id).toEqual(frameAnnotations[0].id);

        const shape = frameToAnnotations[60][0].shape;

        expect(shape.type).toEqual(SHAPE_TYPE_DTO.RECTANGLE);
        if (shape.type === SHAPE_TYPE_DTO.RECTANGLE) {
            expectToBeEqualToPixelAccuracy(shape.x, 300);
            expectToBeEqualToPixelAccuracy(shape.y, 150);
        }

        expect(shape).toEqual(frameToAnnotations[0][0].shape);
        expect(frameToAnnotations[60][0].labels).toEqual(frameToAnnotations[0][0].labels);
    });

    test('merges annotations when propagating to a frame', async ({ page, registerAnnotationsPerFrame }) => {
        const frameToAnnotations = await registerAnnotationsPerFrame({
            0: frameAnnotations,
            60: [
                {
                    id: 'annotation-60-0',
                    shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 400, y: 100, width: 100, height: 100 },
                    labels: frameAnnotations[0].labels,
                    labels_to_revisit: [],
                },
            ],
        });

        const videoPlayerPage = new VideoPlayerPage(page);
        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        // Propagate annotations
        await videoPlayerPage.propagateAnnotations();
        await page.getByRole('button', { name: /merge/i }).click();
        await videoPlayerPage.expectFrameNumberToBeSelected(60);

        // Expect annotations to have been submitted in both the origianl frame and the next frame
        expect(frameToAnnotations[0]).toHaveLength(1);
        expect(frameToAnnotations[60]).toHaveLength(2);

        expect(frameToAnnotations[60][0].id).toEqual('annotation-60-0');
        expect(frameToAnnotations[60][0].shape).toEqual({
            type: SHAPE_TYPE_DTO.RECTANGLE,
            x: 400,
            y: 100,
            width: 100,
            height: 100,
        });
        expect(frameToAnnotations[60][1].id).toEqual(frameAnnotations[0].id);
        expect(frameToAnnotations[60][1].shape).toEqual(frameAnnotations[0].shape);
    });

    test('replaces annotations when propagating to a frame', async ({ page, registerAnnotationsPerFrame }) => {
        const frameToAnnotations = await registerAnnotationsPerFrame({
            0: frameAnnotations,
            60: [
                {
                    id: 'annotation-60-0',
                    shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 400, y: 100, width: 100, height: 100 },
                    labels: frameAnnotations[0].labels,
                    labels_to_revisit: [],
                },
            ],
        });

        const videoPlayerPage = new VideoPlayerPage(page);
        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        // Propagate annotations
        await videoPlayerPage.propagateAnnotations();
        await page.getByRole('button', { name: /replace/i }).click();
        await videoPlayerPage.expectFrameNumberToBeSelected(60);

        // Expect annotations to have been submitted in both the origianl frame and the next frame
        expect(frameToAnnotations[0]).toHaveLength(1);
        expect(frameToAnnotations[60]).toHaveLength(1);

        expect(frameToAnnotations[60][0].id).toEqual(frameAnnotations[0].id);
        expect(frameToAnnotations[60][0].shape).toEqual(frameAnnotations[0].shape);
    });

    test('Task Chain: it is only enabled for "all tasks"', async ({ page, registerAnnotationsPerFrame }) => {
        await registerAnnotationsPerFrame();

        const videoPlayerPage = new VideoPlayerPage(page);
        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        await expect(await videoPlayerPage.getPropagateAnnotationsButton()).toBeEnabled();

        await page.getByRole('navigation', { name: 'navigation-breadcrumbs' }).getByText('Detection').click();
        await expect(await videoPlayerPage.getPropagateAnnotationsButton()).toBeDisabled();

        await page.getByRole('navigation', { name: 'navigation-breadcrumbs' }).getByText('Classification').click();
        await expect(await videoPlayerPage.getPropagateAnnotationsButton()).toBeDisabled();
    });

    test('Propagate should be disabled when the user has invalid annotations', async ({
        page,
        registerApiResponse,
    }) => {
        // Return an invalid annotation, one without labels, so that the propagate annotations button is disabled
        // after loading the annotations.
        registerApiResponse('GetVideoFrameAnnotation', (_, res, ctx) => {
            return res(
                ctx.json({
                    ...userAnnotationsResponse,
                    annotations: [
                        {
                            id: '5d33413a-bf99-4af7-bebb-e30d0c6cfc9f',
                            labels: [],
                            labels_to_revisit: ['610a9065a0d4fbb541cac729'],
                            modified: '2021-08-04T13:06:47.056000+00:00',
                            shape: { height: 20, type: 'RECTANGLE', width: 20, x: 10, y: 10 },
                        },
                    ],
                })
            );
        });
        await page.goto(annotatorUrl);

        const videoPlayerPage = new VideoPlayerPage(page);

        await videoPlayerPage.expectFrameNumberToBeSelected(0);

        await expect(await videoPlayerPage.getPropagateAnnotationsButton()).toBeDisabled();
    });
});
