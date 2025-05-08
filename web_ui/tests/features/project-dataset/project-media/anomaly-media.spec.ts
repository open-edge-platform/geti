// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { range } from 'lodash-es';

import { OpenApiResponseBody } from '../../../../src/core/server/types';
import { paths } from '../../../../src/core/services/routes';
import { delay } from '../../../../src/shared/utils';
import {
    getMockedProjectStatusDTO,
    getMockedProjectStatusTask,
} from '../../../../src/test-utils/mocked-items-factory/mocked-project';
import { expect, test } from '../../../fixtures/base-test';
import { ProjectMediaBucketPage } from '../../../fixtures/page-objects/project-media-bucket-page';
import { resolveAntelopePath } from '../../../utils/dataset';
import { anomalyLabels, project } from './../../../mocks/anomaly/anomaly-classification/anomaly-classification.mocks';

const ANOMALY_LABEL = anomalyLabels.find(({ is_anomalous }) => is_anomalous);

const expectBucketDescription = async (
    bucket: ProjectMediaBucketPage,
    title: string,
    description: string,
    totals: string
) => {
    const bucketLocator = bucket.getBucketLocator();
    await expect(bucketLocator.getByText(title, { exact: true })).toBeVisible();
    await expect(bucketLocator.getByText(description)).toBeVisible();
    await expect(bucketLocator.getByText(totals)).toBeVisible();
};

const url = paths.project.dataset.media({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: '61011e42d891c82e13ec92da',
    projectId: project.id ?? '633035f6c80c9c686fd3bd83',
    datasetId: project.datasets[0].id,
});

test.describe('Anomaly media', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(project));
        });
    });

    test('Normal & anomalous buckets', async ({ page, anomalyMediaPage, registerApiResponse, openApi }) => {
        const uploads = {
            normal: [] as OpenApiResponseBody<'UploadImage'>[],
            anomalous: [] as OpenApiResponseBody<'UploadImage'>[],
        } as const;

        registerApiResponse('UploadImage', async (_request, res, ctx) => {
            const { mock, status } = openApi.mockResponseForOperation('UploadImage');

            // Store uploads locally
            if (uploads['normal'].length < 3) {
                uploads['normal'].push(mock);
            } else {
                uploads['anomalous'].push(mock);
            }

            return res(ctx.status(status), ctx.json(mock));
        });

        registerApiResponse('FilterMedia', (request, res, ctx) => {
            const rules = request.body.rules ?? [];
            const isAnomalous = rules.some(
                (rule) =>
                    rule.field.toLocaleLowerCase() === 'label_id' &&
                    (rule.value as string[]).includes(ANOMALY_LABEL?.id ?? '')
            );

            const datasetUploads =
                rules.length === 0
                    ? [...uploads['normal'], ...uploads['anomalous']]
                    : isAnomalous
                      ? uploads['anomalous']
                      : uploads['normal'];

            return res(
                ctx.json({
                    media: datasetUploads,
                    total_matched_images: datasetUploads.length,
                    total_matched_videos: 0,
                    total_matched_video_frames: 0,
                    total_images: datasetUploads.length,
                    total_videos: 0,
                }),
                ctx.status(200)
            );
        });

        await page.goto(url);

        const files = range(1, 4).map((_) => resolveAntelopePath());

        const normalBucket = await anomalyMediaPage.getNormalBucket();
        await normalBucket.uploadFiles(files);
        await normalBucket.expectTotalMedia({ images: 3 });
        await expectBucketDescription(
            normalBucket,
            'Normal',
            'Normal images are used for model training and evaluation',
            '3 images'
        );

        const anomalousBucket = await anomalyMediaPage.getAnomalousBucket();
        await anomalousBucket.uploadFiles(files);
        await anomalousBucket.expectTotalMedia({ images: 3 });
        await expectBucketDescription(
            anomalousBucket,
            'Anomalous',
            'Anomalous images are used only for model evaluation',
            '3 images'
        );
    });

    test('Start training', async ({ anomalyMediaPage, page, registerApiResponse, openApi }) => {
        // We only show the start training notification if the user has no trained models
        registerApiResponse('GetModelGroups', (_, res, ctx) => {
            return res(ctx.json({ model_groups: [] }));
        });

        registerApiResponse('FilterMedia', async (request, res, ctx) => {
            const { mock } = openApi.mockResponseForOperation('UploadImage');
            const rules = request.body.rules ?? [];

            const anomalyLabel = anomalyLabels.find(({ is_anomalous }) => is_anomalous);
            const isAnomalous = rules.some(
                (rule) =>
                    rule.field.toLocaleLowerCase() === 'label_id' &&
                    (rule.value as string[]).includes(anomalyLabel?.id ?? '')
            );
            const totalImages = isAnomalous ? 3 : 12;

            return res(
                ctx.json({
                    media: range(0, totalImages).map(() => mock),
                    total_matched_images: totalImages,
                    total_matched_videos: 0,
                    total_matched_video_frames: 0,
                    total_images: totalImages,
                    total_videos: 0,
                }),
                ctx.status(200)
            );
        });

        registerApiResponse('GetProjectStatus', (_, res, ctx) => {
            return res(
                // @ts-expect-error Issue in openapi types
                ctx.json(
                    getMockedProjectStatusDTO({
                        tasks: [
                            getMockedProjectStatusTask({
                                id: '60db493fd20945a0046f56d2',
                                title: 'Anomaly detection',
                                ready_to_train: true,
                            }),
                        ],
                    })
                )
            );
        });

        await page.goto(url);
        await anomalyMediaPage.startTrainingFromNotification();

        // Go to models page to see the progress
        await page.getByRole('button', { name: 'Progress', exact: true }).click();
        await expect(page.getByRole('navigation', { name: 'Breadcrumbs' })).toContainText('Models');
    });

    test('It does not show the training notification if the user has trained models', async ({
        page,
        openApi,
        registerApiResponse,
    }) => {
        registerApiResponse('FilterMedia', async (request, res, ctx) => {
            const { mock } = openApi.mockResponseForOperation('UploadImage');

            const rules = request.body.rules ?? [];
            const isAnomalous = rules.some(
                (rule) =>
                    rule.field.toLocaleLowerCase() === 'label_id' &&
                    (rule.value as string[]).includes(ANOMALY_LABEL?.id ?? '')
            );
            const totalImages = isAnomalous ? 3 : 12;

            // Make the filter media request slightly slower, so that it is handled after
            // loading the project's model groups.
            // This is to avoid a (temporary) bug where the notification is shown if the model
            // groups haven't been loaded yet
            await delay(1000);

            return res(
                ctx.json({
                    media: range(0, totalImages).map(() => mock),
                    total_matched_images: totalImages,
                    total_matched_videos: 0,
                    total_matched_video_frames: 0,
                    total_images: totalImages,
                    total_videos: 0,
                }),
                ctx.status(200)
            );
        });

        await page.goto(url);
        await expect(page.getByRole('button', { name: /train/i })).toBeHidden();
    });
});
