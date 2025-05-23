// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { expect, test } from '../../../fixtures/base-test';
import { project as AnomalyProject } from '../../../mocks/anomaly/anomaly-classification/mocks';
import { project as ClassificationProject } from '../../../mocks/classification/classification.mock';
import { project as DetectionSegmentation } from '../../../mocks/detection-segmentation/mocks';

const taskChainProjectUrl = paths.project.dataset.index({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: '61011e42d891c82e13ec92da',
    projectId: DetectionSegmentation.id,
    datasetId: DetectionSegmentation.datasets[0].id,
});

const anomalyProjectUrl = paths.project.dataset.index({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: '61011e42d891c82e13ec92da',
    projectId: AnomalyProject.id,
    datasetId: AnomalyProject.datasets[0].id,
});

const classificationProjectUrl = paths.project.dataset.index({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: '61011e42d891c82e13ec92da',
    projectId: ClassificationProject.id,
    datasetId: ClassificationProject.datasets[0].id,
});

test.describe('Inference using camera', () => {
    test.describe('Task-chain', () => {
        test.beforeEach(async ({ page, cameraPage }) => {
            await page.goto(taskChainProjectUrl);

            await cameraPage.openCameraPage();
            await cameraPage.canTakePhotos();
        });

        test('Take photos', async ({ page, cameraPage }) => {
            await cameraPage.takeSinglePhoto();

            await expect(page.getByLabel(new RegExp(/media item \w+/))).toBeVisible();
            await expect(page.getByLabel(new RegExp(/media item \w+/))).toHaveCount(1);
        });

        test('Deletes photos', async ({ page, cameraPage }) => {
            await cameraPage.takeSinglePhoto();

            await expect(page.getByLabel(new RegExp(/media item \w+/))).toBeVisible();
            await expect(page.getByLabel(new RegExp(/media item \w+/))).toHaveCount(1);

            await cameraPage.deletePhoto();
            await expect(page.getByLabel(new RegExp(/media item \w+/))).toHaveCount(0);
        });

        test('View all thumbnails and discards all', async ({ page, cameraPage }) => {
            // Take 3 photos
            await cameraPage.takeSinglePhoto();
            await cameraPage.takeSinglePhoto();
            await cameraPage.takeSinglePhoto();

            await expect(page.getByLabel(new RegExp(/media item \w+/))).toHaveCount(3);

            await cameraPage.viewAllCaptures();
            await cameraPage.discardAllPhotos();

            await expect(page.getByLabel(new RegExp(/media item \w+/))).toHaveCount(0);
        });
    });

    test.describe('Classification project', () => {
        test.beforeEach(async ({ page, registerApiResponse, cameraPage }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(ClassificationProject)));

            await page.goto(classificationProjectUrl);
            await cameraPage.openCameraPage();
            await cameraPage.canTakePhotos();
        });

        test('Photos can be labelled', async ({ page, cameraPage }) => {
            await cameraPage.takeSinglePhoto();

            await expect(page.getByLabel(new RegExp(/media item \w+/))).toBeVisible();
            await expect(page.getByLabel(new RegExp(/media item \w+/))).toHaveCount(1);

            await page.getByRole('button', { name: 'Select label' }).click();
            await page.getByLabel('label item horse').click();

            await expect(page.getByRole('button', { name: 'horse' })).toBeVisible();
        });
    });

    test.describe('Anomaly project', () => {
        test.beforeEach(async ({ page, registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(AnomalyProject)));

            await page.goto(anomalyProjectUrl);
        });

        test('Photos are correctly labelled', async ({ page, cameraPage }) => {
            // Open camera page for normal bucket
            await cameraPage.openCameraPageAnomaly('normal');

            await cameraPage.canTakePhotos();
            await cameraPage.takeSinglePhoto();

            await expect(page.getByLabel(new RegExp(/media item \w+/))).toBeVisible();
            await expect(page.getByLabel(new RegExp(/media item \w+/))).toHaveCount(1);

            // Has "Normal" label assigned
            await expect(page.getByRole('button', { name: 'Normal' })).toBeVisible();

            await cameraPage.discardAllPhotos();
            await cameraPage.closeCameraPage();

            // Open camera page for anomalous bucket
            await cameraPage.openCameraPageAnomaly('anomalous');

            await cameraPage.canTakePhotos();
            await cameraPage.takeSinglePhoto();

            await expect(page.getByLabel(new RegExp(/media item \w+/))).toBeVisible();
            await expect(page.getByLabel(new RegExp(/media item \w+/))).toHaveCount(1);

            // Has "Normal" label assigned
            await expect(page.getByRole('button', { name: 'Anomalous' })).toBeVisible();
        });
    });
});
