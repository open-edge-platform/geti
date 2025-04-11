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

import { expect } from '@playwright/test';

import { JobState, JobStepState, JobType } from '../../../src/core/jobs/jobs.const';
import { test } from '../../fixtures/base-test';
import { switchCallsAfter } from '../../utils/api';
import { getMockedJob } from '../project-dataset/utils';
import { projects } from './mocks';

const mockedJob = getMockedJob({
    id: '634fbb65d51e114816c68ba2',
});

const job = {
    ...mockedJob,
    steps: [
        {
            index: 1,
            message: 'Preparing project for export',
            progress: -1,
            state: JobStepState.WAITING,
            step_name: 'Exporting project',
        },
    ],
    type: JobType.EXPORT_PROJECT,
    metadata: {
        download_url:
            // eslint-disable-next-line max-len
            '/api/v1/organizations/7e69764d-1494-4ffa-8a5f-d5fb1e4405cd/workspaces/08c04c57-fbdd-486c-b29e-7649739351f0/projects/65bd0c95ab0427f55cf46f0c/exports/65c21375dd00ea723483c880/download',
        include_models: true,
        include_personal_data: true,
        project: {
            id: 'project-id',
            name: 'Project',
        },
    },
};

const SCHEDULED_JOB = { ...job, state: JobState.SCHEDULED };
const RUNNING_JOB = { ...job, state: JobState.RUNNING };
const FINISHED_JOB = { ...job, state: JobState.FINISHED };
const FAILED_JOB = { ...job, state: JobState.FAILED };

test.describe('export project', () => {
    const exportProjectId = '123321';
    const switchAfterOneCall = switchCallsAfter(1);

    test('successful export', async ({ registerApiResponse, page }) => {
        registerApiResponse('GetAllProjectsInAWorkspace', (_, res, ctx) => res(ctx.json(projects)));
        registerApiResponse('TriggerProjectExport', (_, res, ctx) => res(ctx.json({ job_id: exportProjectId })));

        registerApiResponse(
            'GetJob',
            switchAfterOneCall([
                (_, res, ctx) => res(ctx.json(RUNNING_JOB)),
                (_, res, ctx) => res(ctx.json(FINISHED_JOB)),
            ])
        );

        await page.goto('/');
        await page.getByLabel('action menu').click();

        await page.getByText(/export/i).click();

        await expect(page.getByRole('button', { name: 'Download exported project' })).toBeVisible();

        const downloadPromise = page.waitForEvent('download');

        await page.getByRole('button', { name: 'Download exported project' }).click();

        const download = await downloadPromise;
        expect(download).toBeTruthy();
    });

    test('cancel export', async ({ registerApiResponse, page }) => {
        registerApiResponse('GetAllProjectsInAWorkspace', (_, res, ctx) => res(ctx.json(projects)));
        registerApiResponse('TriggerProjectExport', (_, res, ctx) => res(ctx.json({ job_id: exportProjectId })));

        registerApiResponse('GetJob', (_, res, ctx) => res(ctx.json(SCHEDULED_JOB)));

        await page.goto('/');
        await page.getByLabel('action menu').click();
        await page.getByText(/export/i).click();

        await expect(page.getByText('Exporting project: Preparing project for export')).toBeVisible();

        await page.getByLabel('cancel export').click();

        await expect(page.getByText('Exporting project: Preparing project for export')).toBeHidden();
    });

    test('error export', async ({ registerApiResponse, page }) => {
        registerApiResponse('GetAllProjectsInAWorkspace', (_, res, ctx) => res(ctx.json(projects)));
        registerApiResponse('TriggerProjectExport', (_, res, ctx) => res(ctx.json({ job_id: exportProjectId })));

        registerApiResponse(
            'GetJob',
            switchAfterOneCall([
                (_, res, ctx) => res(ctx.json(RUNNING_JOB)),
                (_, res, ctx) => res(ctx.json(FAILED_JOB)),
            ])
        );

        await page.goto('/');
        await page.getByLabel('action menu').click();
        await page.getByText(/export/i).click();

        await expect(page.getByText(/Project was not downloaded due to an error./i)).toBeVisible();
    });
});
