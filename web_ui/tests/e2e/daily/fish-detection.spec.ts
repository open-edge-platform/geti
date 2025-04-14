// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { v4 as uuidv4 } from 'uuid';

import { DatasetTabActions } from '../../../src/pages/project-details/components/project-dataset/utils';
import { expectProjectToHaveLabels, expectProjectToHaveType } from '../../features/project-creation/expect';
import { expect } from '../../fixtures/base-test';
import { VideoPlayerPage } from '../../fixtures/page-objects/annotator/video-player-page';
import { resolveDatasetPath } from '../../utils/dataset';
import { test } from '../fixtures';
import { canAnnotateFishDataset, getFishVideoFiles, loadFishAnnotations, VideoAnnotations } from './../utils';
import { TIMEOUTS } from './timeouts';

test(
    'Simple fish detection project',
    { tag: ['@daily'] },
    async ({
        page,
        workspacesPage,
        mediaPage,
        boundingBoxTool,
        labelShortcutsPage,
        annotatorPage,
        datasetPage,
        projectPage,
    }) => {
        test.skip(canAnnotateFishDataset(), 'this test requires you to setup a local dataset');

        const uniqueSuffix = uuidv4();
        const projectName = `Fish detection - [${uniqueSuffix}]`;

        await page.goto('/');

        await test.step('Create project', async () => {
            console.info('Creating project');
            const detectionLabel = 'Fish';

            const createProjectPage = await workspacesPage.createProject();

            const fishProjectPage = await createProjectPage.detection(projectName, [detectionLabel]);

            await test.step('Verify project was created successfully', async () => {
                await expectProjectToHaveType(fishProjectPage, 'Detection');
                await expectProjectToHaveLabels(fishProjectPage, [detectionLabel]);
            });
        });

        await test.step('Upload media', async () => {
            console.info('Uploading media');
            await page.getByRole('link', { name: /datasets/i }).click();

            const bucket = await mediaPage.getBucket();
            await bucket.uploadFiles(getFishVideoFiles().slice(0, 3));

            await expect(page.getByText(/0 images, 3 videos/i)).toBeVisible({
                timeout: TIMEOUTS.uploadMedia,
            });
            await bucket.expectTotalMedia({ videos: 3 });
        });

        // Annotate enough frames to trigger auto training exactly once
        const AMOUNT_OF_ANNOTATIONS = 12;

        await test.step(`Annotate ${AMOUNT_OF_ANNOTATIONS} frames`, async () => {
            console.info(`Annotating ${AMOUNT_OF_ANNOTATIONS} frames`);
            await page.getByRole('button', { name: /annotate interactively/i }).click();

            await boundingBoxTool.selectTool();

            const videoPage = new VideoPlayerPage(page);
            const videoAnnotations: VideoAnnotations = {};

            for (let idx = 0; idx < AMOUNT_OF_ANNOTATIONS; idx++) {
                const filename = await annotatorPage.selectedMediaFilename();
                loadFishAnnotations(filename, videoAnnotations);

                const frameNumber = await videoPage.getCurrentFrameNumber();
                const annotations = videoAnnotations[filename][frameNumber];

                await page.keyboard.press('Control+a');
                await page.keyboard.press('Delete');

                if (annotations.length === 0) {
                    await (await labelShortcutsPage.getPinnedLabelLocator('No object')).click();

                    // We want to trigger training exactly once, empty labels don't count,
                    // so we repeat once more
                    idx--;
                } else {
                    for (const annotation of annotations) {
                        await boundingBoxTool.drawBoundingBox(annotation.shape);

                        // Deselect the annotation so that when we draw the new annotation
                        // we don't accidentally press on the "Edit label" button
                        await page.keyboard.press('Control+d');
                    }
                }

                const url = page.url();
                await annotatorPage.submit();
                await expect(page).not.toHaveURL(url);
            }

            await annotatorPage.goBackToProjectPage();
        });

        await test.step('importing dataset', async () => {
            const datasetZipPath = resolveDatasetPath('cartoon-fish/fish-detection-testing-set.zip');
            const datasetName = 'Testing set 1';
            console.info(`Import dataset ${datasetName}`);

            // Create new testing set and open the import dataset dialog
            await datasetPage.createDataset();

            const importDatasetDialogPage = await datasetPage.selectDatasetTabMenuItem(
                datasetName,
                DatasetTabActions.ImportDataset
            );

            // Upload the dataset
            await importDatasetDialogPage.uploadDataset(datasetZipPath);

            const timeout = TIMEOUTS.importDataset;

            await page.getByRole('button', { name: /import/i }).click();

            // Wait for the progress to start
            await expect(page.getByText(/Import dataset to project/)).toBeVisible({ timeout });
            await expect(page.getByText(/Waiting.../)).toBeVisible({ timeout });
        });

        await test.step('wait for import & training jobs to finish', async () => {
            // Open jobs dialog
            await page.getByLabel('Jobs in progress').click();

            // Select our project
            await page.getByLabel(/Job scheduler filter project/).fill(projectName);
            await page.getByRole('option', { name: projectName }).click();

            await test.step('Waiting for the import job to finish', async () => {
                await page.getByRole('tab', { name: 'Finished jobs' }).click();
                await expect(
                    page.getByLabel('action-link').getByText('Import Dataset to Existing Project')
                ).toBeVisible({
                    timeout: TIMEOUTS.importDataset,
                });
            });

            await test.step('Waiting for the training job to finish', async () => {
                await expect(page.getByLabel('action-link').getByText('Training')).toBeVisible({
                    timeout: TIMEOUTS.training,
                });
            });

            // Close the dialog
            await page.keyboard.press('Escape');
        });

        await test.step('run a test on imported dataset', async () => {
            // Verify that we have an active model
            const modelsPage = await projectPage.goToModelsPage();

            // Run test on active model's FP16 version
            const activeModel = { name: 'MobileNetV2-ATSS', version: '1' };
            const modelPage = await modelsPage.goToModel(activeModel.name, activeModel.version);
            const runTestDialogPage = await modelPage.openTestDialog(`${activeModel.name} OpenVINO FP16`);

            // Run and inspect tests
            const testName = `Test`;
            await runTestDialogPage.configureTest({ dataset: 'Testing set 1', testName });
            await runTestDialogPage.runTest();

            const testsPage = await modelsPage.seeTestProgress();

            console.info('Waiting for the testing job to finish');
            await testsPage.waitForTestToFinish(testName);

            const testPage = await testsPage.gotoTest(testName);
            const score = await testPage.getScore();

            // The model should be better than throwing a coin
            expect(score).toBeGreaterThanOrEqual(50);
            console.info('Simple Fish detection finished!');
        });
    }
);
