// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ANNOTATIONS_TO_DRAW_PER_ASSET } from './assets-annotations';
import { expectMediaItemToChange } from './expects';
import { expect, test } from './fixtures';
import { getFilesToUpload } from './utils';

const TIMEOUTS = {
    training: 1000 * 60 * 60,
    nextMediaItem: 1000 * 30,
    mediaUploaded: 1000 * 60,
};

test.describe('Model training flow E2E', () => {
    const projectName = `E2E Project - ${new Date().toISOString()}`;

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

            await expect(modelsPage.getRunningModelJob(selectedArchitectureName)).toBeVisible({
                timeout: TIMEOUTS.training,
            });

            await expect(modelsPage.getRunningModelJob(selectedArchitectureName)).toBeHidden({
                timeout: TIMEOUTS.training,
            });

            await expect(modelsPage.getModelInTheList(selectedArchitectureName)).toBeVisible({
                timeout: TIMEOUTS.training,
            });
        });
    });
});
