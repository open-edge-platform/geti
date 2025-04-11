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

import { expect, Page } from '@playwright/test';

import { JobState, JobStepState, JobType } from '../../../src/core/jobs/jobs.const';
import { test } from '../../fixtures/base-test';
import { switchCallsAfter } from '../../utils/api';
import { getMockedJob, projects } from './mocks';

const [project] = projects.projects;

const job = {
    ...getMockedJob({
        id: '634fbb65d51e114816c68ba2',
    }),
    type: JobType.EXPORT_DATASET,
    metadata: {
        project: { id: project.id, name: project.name },
        download_url:
            // eslint-disable-next-line max-len
            'api/v1/organizations/7e69764d-1494-4ffa-8a5f-d5fb1e4405cd/workspaces/08c04c57-fbdd-486c-b29e-7649739351f0/projects/65bd0c95ab0427f55cf46f0c/datasets/65bd0c95ab0427f55cf46f19/exports/65c21375dd00ea723483c880/download',
    },
};

const RUNNING_JOB = { ...job, state: 'running' };
const FINISHED_JOB = { ...job, state: JobState.FINISHED };

const ERROR_MESSAGE = 'Failed exporting the dataset';
const FAILED_JOB = {
    ...job,
    state: JobState.FAILED,
    steps: [
        {
            index: 0,
            message: ERROR_MESSAGE,
            progress: 0.0,
            state: JobStepState.FAILED,
            step_name: 'Export dataset',
        },
    ],
};

const openMenuAndSelectExport = async (page: Page) => {
    await expect(page.getByLabel('open dataset menu')).toBeVisible();
    await page.getByRole('button', { name: /open dataset menu/i }).click();

    const exportOption = page.getByRole('menuitem', { name: /export dataset/i });

    await expect(exportOption).toBeVisible();
    await exportOption.click();
};

const openAndExport = async (page: Page) => {
    await openMenuAndSelectExport(page);

    await page.getByRole('radio', { name: /voc/i }).click();

    await page.getByRole('button', { name: 'Export', exact: true }).click();
};

const assertOpenAndExport = async (page: Page) => {
    await openAndExport(page);

    const datasetsList = page.getByRole('tablist', { name: /dataset page tabs/i });

    const datasetName = await datasetsList.locator('[aria-selected="true"]').getByTestId('dataset-name').textContent();

    await expect(page.getByLabel(/notification toast/i)).toBeVisible();
    await expect(page.getByText(new RegExp(`dataset "${datasetName}" is ready to download.`, 'i'))).toBeVisible();
};

test.describe('export dataset', () => {
    const switchAfterOneCall = switchCallsAfter(1);
    const exportId = job.id;

    test.beforeEach(async ({ registerApiResponse, page }) => {
        registerApiResponse('GetAllProjectsInAWorkspace', (_, res, ctx) => res(ctx.json(projects)));
        registerApiResponse('TriggerDatasetExport', async (_, res, ctx) =>
            res(ctx.json({ export_dataset_id: exportId, status_url: `url/test`, job_id: exportId }))
        );

        registerApiResponse(
            'GetJob',
            switchAfterOneCall([
                (_, res, ctx) => res(ctx.json(RUNNING_JOB)),
                (_, res, ctx) => res(ctx.json(FINISHED_JOB)),
            ])
        );

        await page.goto('/');
        await page.locator(`#project-id-${project.id}`).click();
    });

    test('successful export', async ({ page }) => {
        await assertOpenAndExport(page);

        const downloadButton = page.getByRole('button', { name: /download/i });
        await expect(downloadButton).toBeVisible();

        const [download] = await Promise.all([page.waitForEvent('download'), await downloadButton.click()]);

        expect(await download.failure()).toBeNull();
    });

    test('download option is visible after page reloading', async ({ page }) => {
        await assertOpenAndExport(page);

        await page.reload();

        const downloadButton = page.getByRole('button', { name: /download/i });

        const [download] = await Promise.all([page.waitForEvent('download'), await downloadButton.click()]);

        expect(await download.failure()).toBeNull();
    });

    test('should not show a warning when trying to export again before closing the previous export', async ({
        page,
    }) => {
        await assertOpenAndExport(page);
        await openAndExport(page);

        await expect(page.getByLabel(/notification toast/i)).toBeHidden();
    });

    test('close previous export and show export options', async ({ page }) => {
        await assertOpenAndExport(page);

        const exportStatus = page.getByLabel('export-dataset-download');
        const closeButton = exportStatus.locator('button:has-text("Close")');
        await closeButton.click();

        await openMenuAndSelectExport(page);

        await expect(page.getByRole('heading', { name: /export dataset/i })).toBeVisible();
    });

    test('show status error', async ({ page, registerApiResponse }) => {
        registerApiResponse(
            'GetJob',
            switchAfterOneCall([
                (_, res, ctx) => res(ctx.json(RUNNING_JOB)),
                (_, res, ctx) => res(ctx.json(FAILED_JOB)),
            ])
        );

        await openAndExport(page);

        await expect(page.getByText(ERROR_MESSAGE)).toBeVisible();
    });
});
