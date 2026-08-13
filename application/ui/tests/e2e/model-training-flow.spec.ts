// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { ANNOTATIONS_TO_DRAW_PER_ASSET } from './assets-annotations';
import { expectMediaItemToChange } from './expects';
import { expect, test } from './fixtures';
import { getFilesToUpload } from './utils';

const TIMEOUTS = {
    trainedModelResults: 1000 * 20,
    quantizationResults: 1000 * 20,
    training: 1000 * 60 * 10,
    quantization: 1000 * 60 * 5,
    nextMediaItem: 1000 * 30,
    mediaUploaded: 1000 * 60,
    videoUploaded: 1000 * 60,
    stream: 1000 * 90,
    pipelineHealth: 1000 * 90,
};

const dirname = path.dirname(fileURLToPath(import.meta.url));

/** Uploaded to the backend by the video file source, so this path is only resolved on the test runner. */
const VIDEO_PATH = path.resolve(dirname, '../assets/fish_60.mp4');

test.describe('Model training flow E2E', () => {
    const projectName = `E2E Project - ${new Date().toISOString()}`;
    const uniqueSuffix = new Date().toISOString().replace(/[:.]/g, '-');
    const sourceName = `E2E source - ${uniqueSuffix}`;
    const sinkName = `E2E sink - ${uniqueSuffix}`;

    test.beforeEach(async ({ projectPage }) => {
        await projectPage.disableActivePipeline();
    });

    test.afterEach(async ({ projectPage }) => {
        await test.step('Delete project', async () => {
            await projectPage.gotoList();
            await projectPage.openProjectMenu(projectName);
            await projectPage.clickDeleteMenuAction();
            await projectPage.confirmDeleteProject();

            await expect(projectPage.getProjectCard(projectName)).toBeHidden();
        });
    });

    test('Model training flow', async ({
        projectPage,
        datasetPage,
        annotatorPage,
        boundingBoxTool,
        modelsPage,
        inferencePage,
        streamPage,
        page,
    }) => {
        const filesToUpload = getFilesToUpload('./assets/lego-bricks-dataset');

        await test.step('Navigate to projects list', async () => {
            await projectPage.gotoList();
        });

        await test.step('Create new project', async () => {
            await projectPage.getCreateNewProjectButton().click();
            await projectPage.fillProjectForm({
                name: projectName,
                task: 'detection',
                labelNames: ['minifig', 'motorbike', 'car'],
            });

            await projectPage.getCreateProjectButton().click();
            await expect(page).toHaveURL(/dataset/);
        });

        await test.step('Upload media', async () => {
            await datasetPage.uploadFiles(filesToUpload);

            await expect(datasetPage.getUploadFinishedText(filesToUpload.length)).toBeVisible({
                timeout: TIMEOUTS.mediaUploaded,
            });
        });

        await test.step('Annotate media', async () => {
            await datasetPage.openAnnotator();

            let prevImageName: string | null = null;

            for (let i = 0; i < filesToUpload.length; i++) {
                await expect(annotatorPage.getMediaCanvasLoading()).toBeHidden({ timeout: TIMEOUTS.nextMediaItem });

                await expectMediaItemToChange(annotatorPage, prevImageName, TIMEOUTS.nextMediaItem);

                const imageName = (await annotatorPage.getSelectedMediaItem().getAttribute('alt')) as string;

                prevImageName = imageName;

                const annotations = ANNOTATIONS_TO_DRAW_PER_ASSET[imageName];

                for (const annotation of annotations) {
                    await boundingBoxTool.selectTool();

                    await boundingBoxTool.drawBoundingBox(annotation.shape);

                    const label = page.getByLabel('Labels').getByRole('button', { name: `Label ${annotation.label}` });
                    const isLabelAlreadySelected = (await label.getAttribute('aria-pressed')) === 'true';

                    if (!isLabelAlreadySelected) {
                        await label.click();
                    }
                }

                const saveResponse = await annotatorPage.submitAndWaitForSave();
                expect(saveResponse.ok()).toBeTruthy();
            }

            await annotatorPage.close();
        });

        await test.step('Train model', async () => {
            await page.getByRole('tab', { name: 'Models' }).click();
            await modelsPage.openTrainModelDialog();
            const speedCard = modelsPage.getRecommendedModelArchitectures().getByLabel(/- speed/);

            const selectedArchitectureName = await speedCard.getAttribute('data-architecture-name');

            if (selectedArchitectureName === null) {
                throw new Error('Missing selected architecture name');
            }

            await speedCard.click();
            await modelsPage.startTraining();

            await expect(modelsPage.getRunningJob(selectedArchitectureName)).toBeVisible({
                timeout: TIMEOUTS.training,
            });

            await expect(modelsPage.getRunningJob(selectedArchitectureName)).toBeHidden({
                timeout: TIMEOUTS.training,
            });

            await expect(async () => {
                const modelNames = await modelsPage.getModelNamesInOrder();
                expect(modelNames).toHaveLength(1);
                expect(modelNames.some((name) => name.includes(selectedArchitectureName))).toBe(true);

                const modelAccuracy = await modelsPage
                    .getModelRows()
                    .first()
                    .getByLabel('Model accuracy')
                    .getAttribute('aria-valuenow');

                expect(Number(modelAccuracy)).toBeGreaterThan(0);
            }).toPass({
                timeout: TIMEOUTS.trainedModelResults,
            });
        });

        let modelName = '';

        await test.step('Quantize model', async () => {
            modelName = (await modelsPage.getModelName()) as string;
            await modelsPage.expandModel(modelName);
            await modelsPage.openQuantizationDialog();
            await modelsPage.submitQuantization();

            await expect(modelsPage.getRunningJob(modelName)).toBeVisible({
                timeout: TIMEOUTS.quantization,
            });

            await expect(modelsPage.getRunningJob(modelName)).toBeHidden({
                timeout: TIMEOUTS.quantization,
            });

            const precision = 'INT8';

            await expect(modelsPage.getModelVariantRow(modelName, precision)).toBeVisible({
                timeout: TIMEOUTS.quantizationResults,
            });

            expect(Number(await modelsPage.getModelVariantAccuracy(modelName, precision, precision))).toBeGreaterThan(
                0
            );
        });

        await test.step('Configure the inference pipeline', async () => {
            await inferencePage.openInferenceTab();
            await inferencePage.openPipelineConfiguration();

            const uploadedVideoPath = await inferencePage.addVideoFileSource({
                name: sourceName,
                videoPath: VIDEO_PATH,
                loop: true,
            });
            // The source is only created once the video has finished uploading to the backend.
            await expect(inferencePage.getSourceCard(sourceName)).toBeVisible({ timeout: TIMEOUTS.videoUploaded });

            // The backend rejects a sink folder that does not already exist on its own filesystem, so the
            // directory it just stored the uploaded video in is reused as the output folder.
            const sinkFolderPath = uploadedVideoPath.replace(/[\\/][^\\/]+$/, '');

            await inferencePage.addFolderSink({
                name: sinkName,
                folderPath: sinkFolderPath,
                outputFormats: ['Predictions', 'Image with Predictions'],
            });
            await expect(inferencePage.getSinkCard(sinkName)).toBeVisible();
        });

        await test.step('Select the trained model', async () => {
            // The quantized variant shares this label, so the precision keeps the option unambiguous.
            const openVinoModelName = `${modelName} [FP16]`;

            await inferencePage.selectModel(openVinoModelName);

            await expect(inferencePage.getModelPicker()).toContainText(openVinoModelName);
        });

        await test.step('Enable the pipeline', async () => {
            await expect(inferencePage.getPipelineSwitch('disabled')).toBeVisible();

            await inferencePage.enablePipeline();

            await expect(inferencePage.getPipelineSwitch('enabled')).toBeVisible();
        });

        await test.step('Start the stream', async () => {
            await expect(streamPage.getStartStreamButton()).toBeVisible();

            await streamPage.startStream();

            await expect(streamPage.getStopStreamButton()).toBeVisible({ timeout: TIMEOUTS.stream });
            await expect(streamPage.getStreamVideo()).toBeVisible({ timeout: TIMEOUTS.stream });
        });

        await test.step('Write predictions to the output sink', async () => {
            // The sink writes to a folder on the backend's filesystem, which the runner cannot read when the
            // backend runs on another host. A sink that fails to write turns the pipeline health negative,
            // so a running pipeline is asserted instead of the folder contents.
            await expect(inferencePage.getPipelineHealth()).toHaveText('Running', {
                timeout: TIMEOUTS.pipelineHealth,
            });
        });

        await test.step('Disable the pipeline', async () => {
            await inferencePage.disablePipeline();

            await expect(inferencePage.getPipelineSwitch('disabled')).toBeVisible();
        });
    });
});
