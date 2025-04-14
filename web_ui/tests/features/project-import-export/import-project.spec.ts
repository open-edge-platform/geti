// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { JobState, JobType } from '../../../src/core/jobs/jobs.const';
import { test } from '../../fixtures/base-test';
import { ImportFile } from '../../fixtures/open-api';
import { setTusProgress, switchCallsAfter } from '../../utils/api';
import { loadFile } from '../../utils/dom';
import { getMockedJob } from '../project-dataset/utils';
import { expectRequestProjectImport } from './expect';
import { projects } from './mocks';

const job = {
    ...getMockedJob({
        id: '634fbb65d51e114816c68ba2',
    }),
    type: JobType.IMPORT_PROJECT,
    metadata: {
        download_url:
            // eslint-disable-next-line max-len
            '/api/v1/organizations/7e69764d-1494-4ffa-8a5f-d5fb1e4405cd/workspaces/08c04c57-fbdd-486c-b29e-7649739351f0/projects/65bd0c95ab0427f55cf46f0c/datasets/65bd0c95ab0427f55cf46f19/exports/65c21375dd00ea723483c880/download',
        parameters: {
            file_id: '98754e27-0cc4-4425-a60e-e80889e2d64a',
            skip_signature_verification: false,
            keep_original_dates: false,
        },
        project: {
            id: 'project-id',
            name: 'Project',
        },
    },
};

const RUNNING_JOB = { ...job, state: 'running' };
const FINISHED_JOB = { ...job, state: JobState.FINISHED };

const openImportModal = async (page: Page) => {
    await expect(page.getByLabel('Create project menu')).toBeVisible();

    await page.getByRole('button', { name: /Create project menu/i }).click();
    await page.getByRole('menuitem', { name: /Create from exported project/i }).click();
    await expect(page.getByRole('heading', { name: /import project/i })).toBeVisible();
};

const importFile = async (page: Page, file: ImportFile) => {
    await openImportModal(page);
    await loadFile(page, clickImportProject(page), file);
};

const waitForCreationStatusList = async (page: Page) => {
    await expect(page.getByText(/^project creation -/i)).toBeVisible();
    await expect(getCreationStatusList(page)).toBeVisible();
};

const getCreationStatusList = (page: Page) => page.getByText(/^project creation -/i);
const clickImportProject = (page: Page) => page.getByRole('button', { name: /upload/i }).click();

test.describe('import project', () => {
    const fileSize = 256;
    const requestId = '213-321-123';
    const fileName = 'e2e-file-unique-name.zip';
    const switchAfterTwoCalls = switchCallsAfter(2);
    const switchAfterOneCall = switchCallsAfter(1);
    const jobId = 'c1f02e79-0438-4406-a4bf-fa1426065237';

    test.beforeEach(async ({ registerApiResponse, page }) => {
        registerApiResponse('GetAllProjectsInAWorkspace', (_, res, ctx) => res(ctx.json(projects)));

        registerApiResponse('CreateTusProjectUpload', async (req, res, ctx) =>
            res(ctx.status(200), ctx.set('Location', `http://localhost:3000/api/v1${req.path}/${requestId}`))
        );

        registerApiResponse('ImportProject', async (_, res, ctx) => {
            return res(ctx.json({ job_id: jobId, state: 'finished' }));
        });

        await page.goto('/');
    });

    test('successful import', async ({ page, registerApiResponse }) => {
        registerApiResponse(
            'TusProjectUploadHead',
            switchAfterTwoCalls([
                setTusProgress(fileSize, fileSize / 4),
                setTusProgress(fileSize, fileSize / 2),
                setTusProgress(fileSize, fileSize, 1000),
            ])
        );

        registerApiResponse(
            'GetJob',
            switchAfterOneCall([
                (_, res, ctx) => res(ctx.json(RUNNING_JOB)),
                (_, res, ctx) => res(ctx.json(FINISHED_JOB)),
            ])
        );

        await importFile(page, { name: fileName, size: fileSize });

        await waitForCreationStatusList(page);

        await expect(page.getByText('Uploading...')).toBeVisible();
        await expect(page.getByText('Creating...')).toBeVisible();

        await expectRequestProjectImport(page, jobId);
    });

    test('cancel import', async ({ page, registerApiResponse }) => {
        registerApiResponse(
            'TusProjectUploadHead',
            switchAfterTwoCalls([
                setTusProgress(fileSize, fileSize / 4, 4000),
                setTusProgress(fileSize, fileSize / 2, 4000),
            ])
        );

        await importFile(page, { name: fileName, size: fileSize });

        await waitForCreationStatusList(page);

        await expect(page.getByText('Uploading...')).toBeVisible();
        await page.getByRole('button', { name: /import status menu/i }).click();
        await page.getByText(/cancel/i).click();

        await expect(getCreationStatusList(page)).toBeHidden();
    });

    test('invalid file extension', async ({ page }) => {
        await openImportModal(page);

        await loadFile(page, clickImportProject(page), {
            name: 'invalid-file-extension.png',
            size: fileSize,
        });

        await expect(page.getByText(/Invalid file extension, please try again/i)).toBeVisible();
    });

    test('error during import', async ({ page, registerApiResponse }) => {
        const ERROR_MESSAGE = 'This is an error message';
        const FAILED_JOB = {
            ...job,
            message: '',
            state: JobState.FAILED,
            status: {
                message: ERROR_MESSAGE,
                progress: -1,
                time_remaining: -1,
                state: 'finished',
            },
        };

        registerApiResponse(
            'TusProjectUploadHead',
            switchAfterTwoCalls([
                setTusProgress(fileSize, fileSize / 4),
                setTusProgress(fileSize, fileSize / 2),
                setTusProgress(fileSize, fileSize, 1000),
            ])
        );

        registerApiResponse(
            'GetJob',
            switchAfterOneCall([
                (_, res, ctx) => res(ctx.json(RUNNING_JOB)),
                (_, res, ctx) => res(ctx.json(FAILED_JOB)),
            ])
        );

        await importFile(page, { name: fileName, size: fileSize });

        await waitForCreationStatusList(page);

        await expect(page.getByText('Uploading...')).toBeVisible();
        await expect(page.getByText('Creating...')).toBeVisible();

        await expectRequestProjectImport(page, jobId);
        await expect(page.getByText(/Project is not uploaded due to an error./i)).toBeVisible();
    });

    test.describe('Importing project in on premise environment', () => {
        test.use({
            featureFlags: {
                FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT: true,
            },
        });

        test('import project without verifying its signature', async ({ page, registerApiResponse }) => {
            registerApiResponse(
                'TusProjectUploadHead',
                switchAfterTwoCalls([
                    setTusProgress(fileSize, fileSize / 4),
                    setTusProgress(fileSize, fileSize / 2),
                    setTusProgress(fileSize, fileSize, 1000),
                ])
            );

            registerApiResponse(
                'GetJob',
                switchAfterOneCall([
                    (_, res, ctx) => res(ctx.json(RUNNING_JOB)),
                    (_, res, ctx) => res(ctx.json(FINISHED_JOB)),
                ])
            );

            await openImportModal(page);

            const untrustedSourceAlertMessage = page.getByRole('alert');
            await expect(untrustedSourceAlertMessage).toBeVisible();
            await expect(
                untrustedSourceAlertMessage.getByRole('heading', { name: 'Importing projects from an external source' })
            ).toBeVisible();
            await loadFile(page, clickImportProject(page), { name: fileName, size: fileSize });

            await waitForCreationStatusList(page);

            await expect(page.getByText('Uploading...')).toBeVisible();
            await expect(page.getByText('Creating...')).toBeVisible();

            await expectRequestProjectImport(page, jobId);
        });
    });
});
