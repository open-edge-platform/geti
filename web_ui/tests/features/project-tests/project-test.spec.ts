// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { cloneDeep } from 'lodash-es';
import { v4 as uuidv4 } from 'uuid';

import { OpenApiResponseBody } from '../../../src/core/server/types';
import { test as baseTest, expect } from '../../fixtures/base-test';
import { extendWithOpenApi } from '../../fixtures/open-api';
import { predictionAnnotationsResponse, project, userAnnotationsResponse } from '../../mocks/classification/mocks';
import { expectAGlobalAnnotationToExist } from './expect';

const test = extendWithOpenApi(baseTest);
test.beforeEach(async ({ page, registerApiResponse, openApi }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        return res(ctx.json(cloneDeep(project)));
    });

    registerApiResponse('GetTestInAProject', (_, res, ctx) => {
        const { mock: x, status } = openApi.mockResponseForOperation('GetTestInAProject') as {
            mock: OpenApiResponseBody<'GetTestInAProject'>;
            status: number;
        };

        const mock = cloneDeep(x);

        return res(
            ctx.status(status),
            ctx.json({
                ...mock,
                job_info: { ...mock.job_info, status: 'DONE' },

                scores: [
                    {
                        name: 'F-measure',
                        value: 0.7804878048780486,
                        label_id: null,
                    },
                    {
                        name: 'Precision',
                        value: 0.6666666666666666,
                        label_id: null,
                    },
                    {
                        name: 'Recall',
                        value: 0.9411764705882353,
                        label_id: null,
                    },
                    {
                        name: 'F-measure',
                        value: 0.7804878048780486,
                        label_id: '6101254defba22ca453f11c7',
                    },
                    {
                        name: 'F-measure',
                        value: 0,
                        label_id: '6101254defba22ca453f11c6',
                    },
                ],
                datasets_info: [
                    {
                        ...mock.datasets_info[0],
                        name: 'Testing set 1',
                        n_images: 12,
                        n_frames: 0,
                        n_samples: 12,
                    },
                ],
            })
        );
    });

    registerApiResponse('FilterDataset', (request, res, ctx) => {
        const imagePathPrefix =
            // eslint-disable-next-line max-len
            '/api/v1/organizations/000000000000000000000001/workspaces/60d31793d5f1fb7e6e3c1a4f/projects/60d31793d5f1fb7e6e3c1a50/datasets/62f0c39173cacf6370dbacb7/media/images';

        const { mock, status } = openApi.mockResponseForOperation('FilterDataset') as {
            mock: OpenApiResponseBody<'FilterDataset'>;
            status: number;
        };

        const rules = request.body.rules;

        const isDogLabel = rules.find(
            ({ field, value }) => field === 'label_id' && value === '6101254defba22ca453f11c6'
        );
        const isCatLabel = rules.find(
            ({ field, value }) => field === 'label_id' && value === '6101254defba22ca453f11c7'
        );
        const isHighScore = rules.find(({ field, operator }) => field === 'score' && operator === 'greater_or_equal');

        const cats = isHighScore ? ['cat.11', 'cat.12', 'cat.13'] : ['cat.14', 'cat.15', 'cat.16'];
        const dogs = isHighScore ? ['dog.11', 'dog.12', 'dog.13'] : ['dog.14', 'dog.15', 'dog.16'];

        const media = (isDogLabel ? dogs : isCatLabel ? cats : [...dogs, ...cats]).map((file) => {
            const isVideoFrame = ['dog.11', 'cat.11'].includes(file);
            return {
                annotation_state_per_task: [],
                id: uuidv4(),
                media_information: {
                    display_url: `${imagePathPrefix}/60d31793d5f1fb7e6e3c1a75/display/full`,
                    width: 600,
                    height: 400,
                },
                name: file,
                test_result: {
                    annotation_id: '62f0c39173cacf6370dbacb8',
                    prediction_id: '62f0c39173cacf6370dbacb9',
                    scores: [],
                },
                thumbnail: `${imagePathPrefix}/60d31793d5f1fb7e6e3c1a75/display/thumb`,
                type: isVideoFrame ? 'video_frame' : 'image',
                ...(isVideoFrame ? { frame_index: 0 } : {}),
                upload_time: '2022-08-08T07:26:00.580000+00:00',
                uploader_id: '62f0cfb773cacf6370dbaccd',
            };
        });
        delete mock.next_page;
        mock.total_images = media.length;
        mock.total_matched_images = media.length;
        mock.total_matched_video_frames = 0;
        mock.total_matched_videos = 0;
        mock.total_videos = 0;

        return res(ctx.status(status), ctx.json({ ...mock, media }));
    });

    registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userAnnotationsResponse)));

    registerApiResponse('GetPredictionFromTestInAProject', async (_, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                predictions: predictionAnnotationsResponse.annotations,
            })
        );
    });

    await page.goto(
        // eslint-disable-next-line max-len
        '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/63283aedc80c9c686fd3b1e6/tests/62e38bf55d3d950c738e5615'
    );

    // Wait for page to be loaded
    await expect(page.getByRole('heading', { name: /annotations vs predictions/i })).toBeVisible();
});

test('Filters test results by label', async ({ testPage }) => {
    expect(await testPage.getScore()).toEqual(78);
    expect(await testPage.countImages()).toEqual(12);

    const [cat, dog] = project.pipeline.tasks[1].labels ?? [];

    await testPage.selectLabel(cat.name);
    expect(await testPage.countImages()).toEqual(6);

    await testPage.selectLabel(dog.name);
    expect(await testPage.countImages()).toEqual(6);
});

test('Open annotation vs prediction preview', async ({ page, testPage }) => {
    expect(await testPage.countImages()).toEqual(12);

    await testPage.openMediaPreview('dog.12');
    await expectAGlobalAnnotationToExist(page);

    await testPage.selectAnnotationMode();
    await expectAGlobalAnnotationToExist(page);
    await testPage.selectPredictionMode();
    await expectAGlobalAnnotationToExist(page);

    await testPage.closeMediaPreview();
});

test('Sort images in bucket and check if they are sorted in dataset', async ({ page, testPage }) => {
    expect(await testPage.countImages()).toEqual(12);

    await testPage.sortBucketDescending();

    await testPage.openMediaPreview('dog.14');

    const images = page.getByRole('img', { name: /dog/ });
    await expect(images.nth(0)).toHaveAttribute('alt', 'dog.14');
});

test('Check basic preview information, select image in preview and go next', async ({ page, testPage }) => {
    expect(await testPage.countImages()).toEqual(12);

    await testPage.openMediaPreview('dog.11');

    await testPage.selectItemInPreview('dog.13');
    //Todo: for now I'm checking what I receive from mocked response, some information are missing
    await expect(page.getByTestId('preview-title')).toHaveText('Sample model test @  - Version 1 (undefined)');
    await testPage.selectNextItemInPreview();
    await expect(page.getByTestId('footer')).toHaveText(/cat.11/);
});
