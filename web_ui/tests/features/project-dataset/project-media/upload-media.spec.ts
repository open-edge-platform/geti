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

import { HttpStatusCode } from 'axios';
import range from 'lodash/range';
import take from 'lodash/take';
import takeRight from 'lodash/takeRight';
import OpenAPIBackend from 'openapi-backend';
import { v4 as uuidv4 } from 'uuid';

import { OpenApiResponseBody } from '../../../../src/core/server/types';
import { paths } from '../../../../src/core/services/routes';
import { MEDIA_CONTENT_BUCKET } from '../../../../src/providers/media-upload-provider/media-upload.interface';
import { delay } from '../../../../src/shared/utils';
import { expect, test } from '../../../fixtures/base-test';
import { OpenApiFixtures } from '../../../fixtures/open-api';
import { project as AnomalyProject } from '../../../mocks/anomaly/anomaly-detection/mocks';
import { project as DetectionProject } from '../../../mocks/detection/mocks';
import { switchCallsAfter } from '../../../utils/api';
import { resolveAntelopePath, resolveDatasetPath, resolveMockFilesPath } from '../../../utils/dataset';

const registerFileUploads = (
    registerApiResponse: OpenApiFixtures['registerApiResponse'],
    openApi: OpenAPIBackend,
    beforeUpload?: () => Promise<void>
) => {
    const uploads: OpenApiResponseBody<'UploadImage'>[] = [];

    registerApiResponse('UploadImage', async (_, res, ctx) => {
        const { mock, status } = openApi.mockResponseForOperation('UploadImage');
        const media = { ...mock, id: uuidv4(), name: `Antelope ${uploads.length}` };

        if (beforeUpload) {
            await beforeUpload();
        }

        uploads.push(media);

        return res(ctx.status(status), ctx.json(media));
    });

    registerApiResponse('UploadVideo', async (_, res, ctx) => {
        const { mock, status } = openApi.mockResponseForOperation('UploadImage');
        const media = { ...mock, id: uuidv4(), name: `Antelope ${uploads.length}` };

        if (beforeUpload) {
            await beforeUpload();
        }

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
    return uploads;
};

test.describe('Media upload', () => {
    test.beforeEach(async ({ registerApiResponse, openApi }) => {
        registerFileUploads(registerApiResponse, openApi);
    });

    test.describe('Upload on normal project', () => {
        test.beforeEach(async ({ page, registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => {
                return res(ctx.json(DetectionProject));
            });

            const url = paths.project.dataset.media({
                organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                workspaceId: '61011e42d891c82e13ec92da',
                projectId: DetectionProject.id ?? '633035f6c80c9c686fd3bd83',
                datasetId: DetectionProject.datasets[0].id,
            });

            await page.goto(url);
        });

        test('Upload 1 file', async ({ mediaPage, page }) => {
            const files = [resolveAntelopePath()];
            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(files);

            await expect(page.getByText('Uploaded 1 of 1 file')).toBeVisible();

            await bucket.openDetailsDialog();

            await expect(page.getByText('antelope.png')).toBeVisible();
            await expect(page.getByText('370.9 KB')).toBeVisible();
        });

        test('Upload multiple files one at a time', async ({ mediaPage, page }) => {
            const files = [resolveAntelopePath(), resolveAntelopePath(), resolveAntelopePath()];
            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles([files[0]]);

            await expect(page.getByText('Uploaded 1 of 1 file')).toBeVisible();

            await bucket.uploadFiles([files[1]]);

            await expect(page.getByText('Uploaded 2 of 2 files')).toBeVisible();

            await bucket.uploadFiles([files[2]]);

            await expect(page.getByText('Uploaded 3 of 3 files')).toBeVisible();

            await bucket.openDetailsDialog();

            const dialog = page.getByRole('dialog');
            await expect(dialog.getByText('antelope.png')).toHaveCount(3);
            await expect(dialog.getByText('370.9 KB')).toHaveCount(3);
        });

        test('Upload multiple files at a time (images and videos)', async ({ page, mediaPage }) => {
            const imageFiles = range(0, 4).map((_) => resolveAntelopePath());
            const videoFiles = [resolveDatasetPath('videos/small-vid.mp4')];
            const files = [...imageFiles, videoFiles[0]];

            const bucket = await mediaPage.getBucket();
            await bucket.uploadFiles(files);

            await expect(page.getByText('Uploaded 5 of 5 file')).toBeVisible();
        });

        test('Upload 1 invalid file', async ({ page, mediaPage }) => {
            const files = [resolveMockFilesPath('test.json')];
            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(files);

            await expect(page.getByText('Uploaded 0 of 1 file - 1 error')).toBeVisible();

            await bucket.openDetailsDialog();

            const dialog = page.getByRole('dialog');
            await expect(dialog.getByText('test.json')).toBeVisible();
            await expect(dialog.getByText('20 B')).toBeVisible();
            await expect(dialog.getByRole('link', { name: 'Error' })).toBeVisible();
        });

        test('Upload multiple invalid files', async ({ page, mediaPage }) => {
            const files = [
                resolveMockFilesPath('test.json'),
                resolveMockFilesPath('test.json'),
                resolveMockFilesPath('test.json'),
            ];
            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(files);

            await expect(page.getByText('Uploaded 0 of 3 files - 3 errors')).toBeVisible();

            await bucket.openDetailsDialog();

            const dialog = page.getByRole('dialog');
            await expect(dialog.getByText('test.json')).toHaveCount(3);
            await expect(dialog.getByRole('link', { name: 'Error' })).toHaveCount(3);
        });

        test('Uploads normally if invalid files were uploaded before (images, json)', async ({ page, mediaPage }) => {
            const imageFiles = range(0, 4).map((_) => resolveAntelopePath());
            const invalidFiles = [resolveMockFilesPath('test.json')];
            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(invalidFiles);

            await expect(page.getByText('Uploaded 0 of 1 file - 1 error')).toBeVisible();

            await bucket.uploadFiles(imageFiles);

            await expect(page.getByText('Uploaded 4 of 5 files - 1 error')).toBeVisible();

            await bucket.openDetailsDialog();

            const dialog = page.getByRole('dialog');
            await expect(dialog.getByText('test.json')).toBeVisible();
            await expect(dialog.getByText('20 B')).toBeVisible();
            await expect(dialog.getByRole('link', { name: 'Error' })).toBeVisible();
            await expect(dialog.getByText('antelope.png')).toHaveCount(4);
        });

        test('Uploads normally if invalid files were uploaded before (videos only)', async ({
            page,
            registerApiResponse,
            mediaPage,
            openApi,
        }) => {
            const switchAfterTwoCalls = switchCallsAfter(2);

            const { mock, status } = openApi.mockResponseForOperation('UploadVideo');
            const media = { ...mock, id: uuidv4(), name: `Antelope` };

            registerApiResponse(
                'UploadVideo',
                switchAfterTwoCalls([
                    (_, res, ctx) => res(ctx.status(HttpStatusCode.MethodNotAllowed)),
                    (_, res, ctx) => res(ctx.status(status), ctx.json(media)),
                ])
            );

            const validVideoFile = [resolveDatasetPath('videos/small-vid.mp4')];
            const invalidVideoFile = [resolveDatasetPath('videos/train.m4v')];
            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(invalidVideoFile);

            await expect(page.getByText('Uploaded 0 of 1 file - 1 error')).toBeVisible();

            await bucket.uploadFiles(invalidVideoFile);

            await expect(page.getByText('Uploaded 0 of 2 files - 2 errors')).toBeVisible();

            await bucket.uploadFiles(validVideoFile);

            await expect(page.getByText('Uploaded 1 of 3 files - 2 errors')).toBeVisible();

            await bucket.openDetailsDialog();

            const dialog = page.getByRole('dialog');
            await expect(dialog.getByText('small-vid.mp4')).toBeVisible();
            await expect(dialog.getByRole('link', { name: 'Error' })).toHaveCount(2);
            await expect(dialog.getByText('train.m4v')).toHaveCount(2);
        });

        test('Upload multiple files at a time with some of them invalid', async ({ page, mediaPage }) => {
            const imageFiles = range(0, 4).map((_) => resolveAntelopePath());
            const videoFiles = [resolveDatasetPath('videos/small-vid.mp4')];
            const invalidFiles = [resolveMockFilesPath('test.json')];
            const files = [...imageFiles, ...videoFiles, ...invalidFiles];

            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(files);

            await expect(page.getByText('Uploaded 5 of 6 files - 1 error')).toBeVisible();

            await bucket.openDetailsDialog();

            const dialog = page.getByRole('dialog');
            await expect(dialog.getByText('small-vid.mp4')).toBeVisible();
            await expect(dialog.getByText('test.json')).toBeVisible();
            await expect(dialog.getByText('antelope.png')).toHaveCount(4);
            await expect(dialog.getByRole('link', { name: 'Error' })).toBeVisible();
        });

        test('Cancels all pending uploads', async ({ page, mediaPage, registerApiResponse, openApi }) => {
            registerFileUploads(registerApiResponse, openApi, async () => {
                // Added delay to make sure we upload more files before the previous ones completed
                await delay(3000);
            });

            const imageFiles = [resolveAntelopePath(), resolveAntelopePath()];
            const videoFiles = [resolveDatasetPath('videos/small-vid.mp4')];
            const files = [...imageFiles, ...videoFiles];

            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(files);
            await bucket.openDetailsDialog();
            await bucket.cancelPendingUploads();

            await expect(page.getByText(/Uploaded/)).toBeHidden();
        });

        test('Cancels all pending uploads after uploading a few', async ({
            page,
            mediaPage,
            registerApiResponse,
            openApi,
        }) => {
            registerFileUploads(registerApiResponse, openApi, async () => {
                // Added delay to make sure we upload more files before the previous ones completed
                await delay(3000);
            });

            const imageFiles = [resolveAntelopePath(), resolveAntelopePath()];
            const videoFiles = [resolveDatasetPath('videos/small-vid.mp4')];
            const files = [...videoFiles, ...imageFiles];

            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(files);
            await bucket.openDetailsDialog();

            // Wait for 1 upload to succeed and cancel the rest
            await delay(3000);
            await bucket.cancelPendingUploads();

            await expect(page.getByText('Uploaded 1 of 1 file')).toBeVisible();
        });

        test('Uploads more from the dialog', async ({ page, mediaPage }) => {
            const imageFiles = [resolveAntelopePath()];
            const videoFiles = [resolveDatasetPath('videos/small-vid.mp4')];

            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(imageFiles);
            await bucket.openDetailsDialog();

            await page.getByRole('button', { name: /upload more/i }).click();

            const [fileChooser] = await Promise.all([
                page.waitForEvent('filechooser'),
                page.getByRole('menuitem', { name: /files/i }).click(),
            ]);

            await fileChooser.setFiles(videoFiles);

            const dialog = page.getByRole('dialog');
            await expect(dialog.getByText('small-vid.mp4')).toBeVisible();
            await expect(dialog.getByText('antelope.png')).toBeVisible();
        });

        test('Uploads multiple folders at the same time', async ({ page, mediaPage, openApi, registerApiResponse }) => {
            registerFileUploads(registerApiResponse, openApi, async () => {
                // Added delay to make sure we upload more files before the previous ones completed
                await delay(3000);
            });

            const imageFiles = [resolveAntelopePath(), resolveAntelopePath()];
            const videoFiles = [resolveDatasetPath('videos/small-vid.mp4')];
            const files = [...imageFiles, ...videoFiles];

            const bucket = await mediaPage.getBucket();

            // Upload the same batch of files three times
            await bucket.uploadFiles(files);
            await bucket.uploadFiles(files);
            await bucket.uploadFiles(files);

            await bucket.openDetailsDialog();

            await expect(async () => {
                await expect(page.getByText('small-vid.mp4')).toHaveCount(3);
                await expect(page.getByText('antelope.png')).toHaveCount(6);
            }).toPass();
        });

        test('Shows the error message when the upload fails because of server validation', async ({
            mediaPage,
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('UploadVideo', (_, res, ctx) => res(ctx.status(HttpStatusCode.UnsupportedMediaType)));

            registerApiResponse('UploadImage', (_, res, ctx) => res(ctx.status(HttpStatusCode.UnsupportedMediaType)));

            const imgFiles = [resolveAntelopePath(), resolveAntelopePath()];

            // Assuming video is too long (as of now, longer than 3 hours)
            const videoFile = [resolveDatasetPath('videos/small-vid.mp4')];

            const bucket = await mediaPage.getBucket();

            await bucket.uploadFiles(videoFile);

            await expect(page.getByText('Uploaded 0 of 1 file - 1 error')).toBeVisible();

            await bucket.uploadFiles(imgFiles);

            await expect(page.getByText('Uploaded 0 of 3 files - 3 errors')).toBeVisible();
        });
    });

    test.describe('Upload anomaly project', () => {
        test.beforeEach(async ({ page, registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => {
                return res(ctx.json(AnomalyProject));
            });

            const anomalyProjectUrl = paths.project.dataset.media({
                organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                workspaceId: '61011e42d891c82e13ec92da',
                projectId: AnomalyProject.id ?? '633035f6c80c9c686fd3bd83',
                datasetId: AnomalyProject.datasets[0].id,
            });

            await page.goto(anomalyProjectUrl);
        });

        test('Upload files on one bucket only', async ({ page, mediaPage }) => {
            const files = [resolveAntelopePath()];
            const bucket = await mediaPage.getBucket(MEDIA_CONTENT_BUCKET.NORMAL);

            await bucket.uploadFiles(files);

            await expect(page.getByText('Uploaded 1 of 1 file')).toBeVisible();

            await bucket.openDetailsDialog();

            await expect(page.getByText('antelope.png')).toBeVisible();
            await expect(page.getByText('370.9 KB')).toBeVisible();
        });

        test('Upload files on both buckets', async ({ page, mediaPage }) => {
            const imageFiles = range(0, 4).map((_) => resolveAntelopePath());
            const normalBucket = await mediaPage.getBucket(MEDIA_CONTENT_BUCKET.NORMAL);
            const anomalousBucket = await mediaPage.getBucket(MEDIA_CONTENT_BUCKET.ANOMALOUS);

            await normalBucket.uploadFiles([...take(imageFiles, 2)]);

            await expect(page.getByText('Uploaded 2 of 2 file')).toBeVisible();

            await anomalousBucket.uploadFiles([...takeRight(imageFiles, 2)]);

            await expect(page.getByText('Uploaded 4 of 4 file')).toBeVisible();

            await anomalousBucket.openDetailsDialog();

            await expect(page.getByText('antelope.png')).toHaveCount(4);
        });

        test('Upload files on both buckets at the same time', async ({
            registerApiResponse,
            page,
            mediaPage,
            openApi,
        }) => {
            registerFileUploads(registerApiResponse, openApi, async () => {
                await delay(1000);
            });

            const imageFiles = range(0, 4).map((_) => resolveAntelopePath());
            const normalBucket = await mediaPage.getBucket(MEDIA_CONTENT_BUCKET.NORMAL);
            const anomalousBucket = await mediaPage.getBucket(MEDIA_CONTENT_BUCKET.ANOMALOUS);

            await normalBucket.uploadFiles([...take(imageFiles, 2)]);
            await anomalousBucket.uploadFiles([...takeRight(imageFiles, 2)]);

            await expect(page.getByText('Uploaded 4 of 4 file')).toBeVisible();

            await anomalousBucket.openDetailsDialog();

            await expect(page.getByText('antelope.png')).toHaveCount(4);
        });

        test('Upload multiple files concurrently with some invalid', async ({
            page,
            registerApiResponse,
            openApi,
            mediaPage,
        }) => {
            registerFileUploads(registerApiResponse, openApi, async () => {
                await delay(1000);
            });

            const imageFiles = range(0, 4).map((_) => resolveAntelopePath());
            const invalidFiles = [resolveMockFilesPath('test.json')];
            const videoFiles = [resolveDatasetPath('videos/small-vid.mp4')];

            const normalBucket = await mediaPage.getBucket(MEDIA_CONTENT_BUCKET.NORMAL);
            const anomalousBucket = await mediaPage.getBucket(MEDIA_CONTENT_BUCKET.ANOMALOUS);

            await normalBucket.uploadFiles([...imageFiles, ...invalidFiles]);
            await anomalousBucket.uploadFiles([...videoFiles]);

            await expect(page.getByText('Uploaded 5 of 6 files - 1 error')).toBeVisible();

            await anomalousBucket.openDetailsDialog();

            await expect(page.getByText('antelope.png')).toHaveCount(4);
            await expect(page.getByText('small-vid.mp4')).toHaveCount(1);
        });
    });
});
