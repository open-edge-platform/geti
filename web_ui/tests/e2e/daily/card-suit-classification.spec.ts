// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import fs from 'fs';

import { v4 as uuidv4 } from 'uuid';

import { DatasetTabActions } from '../../../src/pages/project-details/components/project-dataset/utils';
import { expectProjectToHaveLabels, expectProjectToHaveType } from '../../features/project-creation/expect';
import { expect } from '../../fixtures/base-test';
import { resolveDatasetPath } from '../../utils/dataset';
import { test } from '../fixtures';
import { TIMEOUTS } from './timeouts';

test(
    'Simple Card classification',
    { tag: ['@daily'] },
    async ({ workspacesPage, page, mediaPage, projectPage, datasetPage }) => {
        await page.goto('/');

        const uniqueSuffix = uuidv4();
        const projectName = `Card suit classification - [${uniqueSuffix}]`;
        const classificationLabels: Record<string, string[]> = {
            Suit: ['Hearts', 'Diamonds', 'Spades', 'Clubs'],
        };

        await test.step('create project', async () => {
            const createProjectPage = await workspacesPage.createProject();

            const cardProjectPage = await createProjectPage.classificationHierarchical(
                projectName,
                classificationLabels
            );

            await test.step('Verify project was created successfully', async () => {
                const labels = Object.keys(classificationLabels).flatMap((group) => classificationLabels[group]);

                await expectProjectToHaveType(cardProjectPage, 'Classification');
                await expectProjectToHaveLabels(cardProjectPage, labels);
            });
        });

        await test.step('importing media', async () => {
            await projectPage.goToDatasetPage();

            const bucket = await mediaPage.getBucket();

            let totalFiles = 0;
            for (const suit of classificationLabels['Suit']) {
                await test.step(`Uploading "${suit}"`, async () => {
                    const path = resolveDatasetPath(`cards/${suit.toLocaleLowerCase()}`);

                    // Take 12 images per suit so that we train with minimal images
                    const files = fs
                        .readdirSync(path)
                        .map((filename) => resolveDatasetPath(path, filename))
                        .slice(0, 12);

                    await bucket.uploadFiles(files, [suit]);

                    totalFiles += files.length;

                    await expect(async () => {
                        const message = page.getByText(new RegExp(`Uploaded ${totalFiles} of ${totalFiles} files`));
                        await expect(message).toBeVisible();
                    }).toPass({
                        timeout: TIMEOUTS.uploadMedia,
                    });

                    await bucket.expectTotalMedia({ images: totalFiles });
                });
            }
        });

        await test.step('importing dataset', async () => {
            const datasetZipPath = resolveDatasetPath('cards/card-suit-classification-dataset.zip');
            const datasetName = 'Testing set 1';

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

            // Open 'Finished jobs' tab and verify that both train and import jobs are there
            await page.getByRole('tab', { name: 'Finished jobs' }).click();

            await test.step('Waiting for the import job to finish', async () => {
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
            const activeModel = { name: 'EfficientNet-B0', version: '1' };
            const modelPage = await modelsPage.goToModel(activeModel.name, activeModel.version);
            const runTestDialogPage = await modelPage.openTestDialog(`${activeModel.name} OpenVINO FP16`);

            // Run and inspect tests
            const testName = `Test`;
            await runTestDialogPage.configureTest({ dataset: 'Testing set 1', testName });
            await runTestDialogPage.runTest();

            const testsPage = await modelsPage.seeTestProgress();

            await test.step('Waiting for the testing job to finish', async () => {
                await testsPage.waitForTestToFinish(testName);
            });

            const testPage = await testsPage.gotoTest(testName);
            const score = await testPage.getScore();

            // The model should be better than just throwing a coin
            expect(score).toBeGreaterThanOrEqual(25);
            console.info('Simple Card classification finished!');
        });
    }
);
