// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { DatasetStatisticsView } from '@/api/types';

import { ANNOTATIONS_TO_DRAW_PER_ASSET } from './assets-annotations';
import { expect, test } from './fixtures';
import { annotateMediaItems, getAssetName, getFilesToUpload, isZipFile } from './utils';

const TIMEOUTS = {
    nextMediaItem: 1000 * 30,
    mediaUploaded: 1000 * 60,
    export: 1000 * 60 * 5,
    importPreparation: 1000 * 60 * 5,
    import: 1000 * 60 * 5,
};

// Keeps the export and import jobs short while still covering items with several annotations.
const MEDIA_COUNT = 3;

const sortNumbers = (values: number[]) => values.toSorted((a, b) => a - b);

test.describe('Dataset export and import E2E', () => {
    const uniqueSuffix = new Date().toISOString().replace(/[:.]/g, '-');
    const sourceProjectName = `E2E Export - ${uniqueSuffix}`;
    const importedProjectName = `E2E Import - ${uniqueSuffix}`;

    test.afterEach(async ({ projectPage }) => {
        await test.step('Delete projects', async () => {
            await projectPage.gotoList();
            await projectPage.waitForProjectList();

            for (const projectName of [sourceProjectName, importedProjectName]) {
                if (!(await projectPage.getProjectCard(projectName).isVisible())) {
                    continue;
                }

                await projectPage.openProjectMenu(projectName);
                await projectPage.clickDeleteMenuAction();
                await projectPage.confirmDeleteProject();

                await expect(projectPage.getProjectCard(projectName)).toBeHidden();
            }
        });
    });

    test('Exported dataset can be imported as a new project', async ({
        projectPage,
        datasetPage,
        importDatasetPage,
        annotatorPage,
        boundingBoxTool,
        page,
    }, testInfo) => {
        const filesToUpload = getFilesToUpload('./assets/lego-bricks-dataset').slice(0, MEDIA_COUNT);
        const drawnAnnotations = filesToUpload.flatMap((file) => ANNOTATIONS_TO_DRAW_PER_ASSET[getAssetName(file)]);
        const usedLabelNames = [...new Set(drawnAnnotations.map(({ label }) => label))];
        const drawnBoxesPerLabel = usedLabelNames.map(
            (labelName) => drawnAnnotations.filter(({ label }) => label === labelName).length
        );

        let exportedDatasetPath = '';

        await test.step('Create an annotated project', async () => {
            await projectPage.gotoList();
            await projectPage.getCreateNewProjectButton().click();
            await projectPage.fillProjectForm({
                name: sourceProjectName,
                task: 'detection',
                labelNames: ['minifig', 'motorbike', 'car'],
            });
            await projectPage.getCreateProjectButton().click();
            await expect(page).toHaveURL(/dataset/);

            await datasetPage.uploadFiles(filesToUpload);
            await expect(datasetPage.getUploadFinishedText(filesToUpload.length)).toBeVisible({
                timeout: TIMEOUTS.mediaUploaded,
            });

            await datasetPage.openAnnotator();
            await annotateMediaItems({
                page,
                annotatorPage,
                boundingBoxTool,
                count: filesToUpload.length,
                timeout: TIMEOUTS.nextMediaItem,
            });
            await annotatorPage.close();
        });

        await test.step('Export the dataset', async () => {
            await page.getByRole('button', { name: 'import export dataset' }).click();
            await page.getByRole('menuitem', { name: 'Export dataset', exact: true }).click();
            await page.getByRole('dialog').getByRole('button', { name: 'Export', exact: true }).click();

            const downloadButton = page.getByRole('button', { name: 'download dataset' });
            await expect(downloadButton).toBeEnabled({ timeout: TIMEOUTS.export });

            const downloadPromise = page.waitForEvent('download');
            await downloadButton.click();
            const download = await downloadPromise;

            exportedDatasetPath = testInfo.outputPath(download.suggestedFilename());
            await download.saveAs(exportedDatasetPath);

            expect(await isZipFile(exportedDatasetPath)).toBe(true);

            await page.getByRole('button', { name: 'close export dataset status' }).click();
        });

        await test.step('Import the exported dataset as a new project', async () => {
            await projectPage.gotoList();
            await page.getByRole('button', { name: 'Create from dataset' }).click();
            await importDatasetPage.uploadZipFile(exportedDatasetPath);

            const dialog = importDatasetPage.getDialog();
            const projectNameInput = dialog.getByRole('textbox', { name: 'Project name' });

            await expect(projectNameInput).toBeVisible({ timeout: TIMEOUTS.importPreparation });
            await projectNameInput.fill(importedProjectName);
            await expect(dialog.getByRole('button', { name: /Object detection \(Recommended\)/ })).toBeVisible();
            await dialog.getByRole('button', { name: 'Next' }).click();

            await expect(importDatasetPage.getStatisticsHeading()).toBeVisible();
            for (const labelName of usedLabelNames) {
                await expect(dialog.getByText(labelName, { exact: true })).toBeVisible();
            }

            await dialog.getByRole('button', { name: 'Create' }).click();
            await expect(dialog).toBeHidden();

            await expect(page.getByText(/imported successfully/)).toBeVisible({ timeout: TIMEOUTS.import });
        });

        await test.step('Imported project keeps media and annotations', async () => {
            const statisticsResponse = page.waitForResponse(
                (response) =>
                    response.request().method() === 'GET' &&
                    new URL(response.url()).pathname.endsWith('/dataset/statistics')
            );

            await projectPage.gotoList();
            await projectPage.openProject(importedProjectName);
            await expect(page).toHaveURL(/dataset/);

            await expect(datasetPage.getImagesCountText(MEDIA_COUNT)).toBeVisible();

            await page.getByRole('button', { name: 'dataset statistics' }).click();

            // Label ids differ between projects and media is renamed on import, so only the counts are compared.
            const { annotations_counts } = (await (await statisticsResponse).json()) as DatasetStatisticsView;
            const importedBoxesPerLabel = annotations_counts.instances_per_label
                .map(({ instances }) => instances)
                .filter((instances) => instances > 0);

            expect(annotations_counts.annotated_images).toBe(MEDIA_COUNT);
            expect(annotations_counts.instances).toBe(drawnAnnotations.length);
            expect(sortNumbers(importedBoxesPerLabel)).toEqual(sortNumbers(drawnBoxesPerLabel));
        });
    });
});
