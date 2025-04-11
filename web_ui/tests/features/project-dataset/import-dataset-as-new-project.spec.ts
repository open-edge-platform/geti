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

import { expect, Locator, Page } from '@playwright/test';
import { MockedResponse, ResponseComposition, RestContext } from 'msw';

import { DATASET_IMPORT_WARNING_TYPE } from '../../../src/core/datasets/dataset.enum';
import { DatasetImportWarningDTO } from '../../../src/core/datasets/dtos/dataset.interface';
import { JobState, JobStepState } from '../../../src/core/jobs/jobs.const';
import { OpenApiRequest } from '../../../src/core/server/types';
import { test } from '../../fixtures/base-test';
import { registerJobList, setTusProgress } from '../../utils/api';
import { loadFile } from '../../utils/dom';
import { cancelJobFromJobScheduler } from '../job-scheduler/utils';
import { projects, supportedProjectTypesSingleTask, supportedProjectTypesTaskChained } from './mocks';
import {
    getLocalStorage,
    getMockedImportingJob,
    getMockedPreparingJob,
    registerJobResponses,
    waitForJobToFinish,
} from './utils';

const WORKSPACE_ID = '61011e42d891c82e13ec92da';
const ORGANIZATION_ID = '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633';

const clickNext = (page: Page) => page.getByRole('button', { name: /next/i }).click();
const clickCreate = (page: Page) => page.getByRole('button', { name: /create/i }).click();

const openImportModal = async (page: Page) => {
    await expect(page.getByRole('button', { name: /Create project menu/i })).toBeVisible();
    await page.getByRole('button', { name: /Create project menu/i }).click();
    await page.getByRole('menuitem', { name: /create from dataset/i }).click();
    await expect(page.getByRole('heading', { name: /create project from a dataset - import/i })).toBeVisible();
};

const fillProjectNameAndType = async (page: Page, projectName: string, type: string | RegExp) => {
    await expect(page.getByRole('textbox', { name: /project name/i })).toBeVisible();
    await page.getByRole('textbox', { name: /project name/i }).fill(projectName);
    await page.getByRole('button', { name: /show suggestions/i }).click();
    await page.getByRole('option', { name: type }).click();
};

const hideImportModal = (page: Page) => page.getByRole('button', { name: /hide/i }).click();
const clickUpload = (page: Page) => page.getByRole('button', { name: /upload/i }).click();

const getDetectionGroupLabel = (page: Page): Locator => page.getByText('Detection Task Labels');
const getSegmentationGroupLabel = (page: Page): Locator => page.getByText('Segmentation Task Labels');

test.describe('Import dataset as new project', (): void => {
    const fileSize = 256;
    const uploadId = '123-321-213';
    const projectName = 'project name test';
    const fileName = 'e2e file unique name';

    const importWarning: DatasetImportWarningDTO = {
        affected_images: 10,
        description: 'Image contains no annotation for detection domain',
        name: 'Missing annotation for detection domain',
        type: 'warning' as DATASET_IMPORT_WARNING_TYPE,
    };

    const preparingJobId = '651bd77c1b63044e0b08b140a';
    const importingJobId = '651bd77c1b63044e0b08b140b';

    const mockedStep = {
        index: 1,
        progress: 10,
        step_name: 'Test step',
        state: JobStepState.RUNNING,
        message: 'testing message',
    };

    const mockedImportingStep = {
        index: 1,
        progress: 100,
        state: JobStepState.RUNNING,
        step_name: 'Create project from import dataset',
        message: 'Project created and populated successfully',
    };

    test.describe('SINGLE TASK', () => {
        test.beforeEach(async ({ registerApiResponse, page }) => {
            registerApiResponse(
                'GetAllProjectsInAWorkspace',
                (
                    _: OpenApiRequest<'GetAllProjectsInAWorkspace'>,
                    res: ResponseComposition<Record<string, unknown>>,
                    ctx: RestContext
                ) => res(ctx.json(projects))
            );

            registerApiResponse(
                'CreateTusDatasetUpload',
                async (
                    req: OpenApiRequest<'CreateTusDatasetUpload'>,
                    res: ResponseComposition<Record<string, unknown>>,
                    ctx: RestContext
                ): Promise<MockedResponse> =>
                    res(ctx.status(200), ctx.set('Location', `http://localhost:3000/api/v1${req.path}/${uploadId}`))
            );

            registerApiResponse(
                'PrepareDatasetForImport',
                (
                    _: OpenApiRequest<'PrepareDatasetForImport'>,
                    res: ResponseComposition<Record<string, unknown>>,
                    ctx: RestContext
                ) => res(ctx.json({ supported_project_types: supportedProjectTypesSingleTask, warnings: [] }))
            );

            registerApiResponse('TusDatasetUploadHead', setTusProgress(fileSize, fileSize));

            registerApiResponse('PrepareDatasetForImport', (_, res, ctx) => res(ctx.json({ job_id: preparingJobId })));
            registerApiResponse('ImportProjectFromDataset', (_, res, ctx) => res(ctx.json({ job_id: importingJobId })));

            await page.goto('/');
        });

        test.describe('import successful', (): void => {
            test('warnings', async ({ page, registerApiResponse }) => {
                const { project_type } = supportedProjectTypesSingleTask[0];
                await openImportModal(page);

                registerJobResponses(registerApiResponse, preparingJobId, getMockedPreparingJob, {
                    steps: [mockedStep],
                    metadata: {
                        warnings: [importWarning],
                        supported_project_types: supportedProjectTypesSingleTask,
                    },
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                    loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
                ]);

                await expect(
                    page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
                ).toBeVisible();
                await waitForJobToFinish(page, preparingJobId);

                await expect(page.getByRole('heading', { name: 'Detected issues in the dataset' })).toBeVisible();
                await clickNext(page);

                await fillProjectNameAndType(page, projectName, new RegExp(project_type, 'i'));
                await clickNext(page);

                registerJobResponses(registerApiResponse, importingJobId, getMockedImportingJob, {
                    steps: [mockedImportingStep],
                    metadata: {
                        project_id: '123321',
                    },
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${importingJobId}`)),
                    clickCreate(page),
                ]);
                await expect(
                    page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
                ).toBeVisible();

                await waitForJobToFinish(page, importingJobId);

                await expect(
                    page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
                ).toBeHidden();
            });

            test('no warnings', async ({ page, registerApiResponse }) => {
                const { project_type } = supportedProjectTypesSingleTask[0];
                await openImportModal(page);

                registerJobResponses(registerApiResponse, preparingJobId, getMockedPreparingJob, {
                    steps: [mockedStep],
                    metadata: {
                        warnings: [],
                        supported_project_types: supportedProjectTypesSingleTask,
                    },
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                    loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
                ]);

                await expect(
                    page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
                ).toBeVisible();
                await waitForJobToFinish(page, preparingJobId);

                await fillProjectNameAndType(page, projectName, new RegExp(project_type, 'i'));

                await clickNext(page);

                registerJobResponses(registerApiResponse, importingJobId, getMockedImportingJob, {
                    steps: [mockedImportingStep],
                    metadata: {
                        project_id: '123321',
                    },
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${importingJobId}`)),
                    clickCreate(page),
                ]);
                await expect(
                    page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
                ).toBeVisible();

                await waitForJobToFinish(page, importingJobId);

                await expect(
                    page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
                ).toBeHidden();
            });
        });

        test.describe('preparing job status', (): void => {
            test('cancel', async ({ page, registerApiResponse }) => {
                await openImportModal(page);

                registerJobResponses(registerApiResponse, preparingJobId, getMockedPreparingJob, {
                    steps: [mockedStep],
                    metadata: {
                        warnings: [],
                        supported_project_types: supportedProjectTypesSingleTask,
                    },
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                    loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
                ]);

                await expect(
                    page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
                ).toBeVisible();

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}:cancel`)),
                    page.getByRole('button', { name: 'Cancel' }).click(),
                ]);

                await expect(page.getByText('Create project from a dataset - Import')).toBeHidden();
                await expect(page.getByLabel('dataset-import-panel')).toBeHidden();
            });

            test('cancel import from job list', async ({ page, registerApiResponse }) => {
                const preparingJob = getMockedPreparingJob({
                    id: preparingJobId,
                    name: 'Test preparing importing',
                    state: JobState.SCHEDULED,
                });

                registerJobList(registerApiResponse, preparingJob);

                await openImportModal(page);

                await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

                await hideImportModal(page);

                expect(
                    await getLocalStorage(page, `importDatasetToNewProject-${ORGANIZATION_ID}-${WORKSPACE_ID}`)
                ).toHaveLength(1);
                await expect(page.getByLabel('dataset-import-panel')).toBeVisible();

                await cancelJobFromJobScheduler(preparingJob, page);

                await expect(page.getByLabel('dataset-import-panel')).toBeHidden();
                expect(
                    await getLocalStorage(page, `importDatasetToNewProject-${ORGANIZATION_ID}-${WORKSPACE_ID}`)
                ).toHaveLength(0);
            });

            test('error', async ({ page, registerApiResponse }) => {
                await openImportModal(page);
                const mockedFailedStep = {
                    index: 1,
                    progress: 10,
                    step_name: 'Test step',
                    state: JobStepState.RUNNING,
                    message: 'Something went wrong. step',
                };

                registerJobResponses(registerApiResponse, preparingJobId, getMockedPreparingJob, {
                    steps: [mockedFailedStep],
                    state: JobState.FAILED,
                    metadata: {},
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                    loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
                ]);

                await waitForJobToFinish(page, preparingJobId, JobState.FAILED);

                await expect(page.getByText('Dataset has not been prepared')).toBeVisible();
                await expect(page.getByText(mockedFailedStep.message)).toBeVisible();

                await page.reload();

                await expect(page.getByText('Preparing error')).toBeVisible();

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                    page.getByRole('button', { name: 'Try again' }).click(),
                ]);
            });
        });

        test.describe('importing job status', (): void => {
            const { project_type } = supportedProjectTypesSingleTask[0];

            test('cancel', async ({ page, registerApiResponse }) => {
                await openImportModal(page);

                registerJobResponses(registerApiResponse, preparingJobId, getMockedPreparingJob, {
                    steps: [mockedStep],
                    metadata: {
                        warnings: [],
                        supported_project_types: supportedProjectTypesSingleTask,
                    },
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                    loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
                ]);

                await expect(
                    page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
                ).toBeVisible();
                await waitForJobToFinish(page, preparingJobId);

                await fillProjectNameAndType(page, projectName, new RegExp(project_type, 'i'));

                await clickNext(page);

                registerJobResponses(registerApiResponse, importingJobId, getMockedImportingJob, {
                    steps: [mockedImportingStep],
                    metadata: {
                        project_id: '123321',
                    },
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${importingJobId}`)),
                    clickCreate(page),
                ]);

                await expect(
                    page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
                ).toBeVisible();
                await page.getByRole('button', { name: 'dataset-import-menu' }).click();

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${importingJobId}:cancel`)),
                    page.getByRole('menuitem', { name: /cancel/i }).click(),
                ]);

                await expect(page.getByText('Create project from a dataset - Import')).toBeHidden();
                await expect(page.getByText('dataset-import-panel')).toBeHidden();
            });

            test('cancel import from job list', async ({ page, registerApiResponse }) => {
                const preparingJob = getMockedPreparingJob({
                    id: preparingJobId,
                    name: 'Test preparing dataset',
                    state: JobState.FINISHED,
                    metadata: {
                        warnings: [],
                        supported_project_types: supportedProjectTypesSingleTask,
                    },
                });

                const importingJob = getMockedImportingJob({
                    id: importingJobId,
                    name: 'Test importing dataset',
                    state: JobState.SCHEDULED,
                });

                registerJobList(registerApiResponse, preparingJob);

                await openImportModal(page);

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                    loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
                ]);
                await waitForJobToFinish(page, preparingJob.id);

                registerJobList(registerApiResponse, importingJob);
                await fillProjectNameAndType(page, projectName, new RegExp(project_type, 'i'));
                await clickNext(page);

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${importingJob.id}`)),
                    clickCreate(page),
                ]);

                await expect(page.getByLabel('dataset-import-panel')).toBeVisible();
                expect(
                    await getLocalStorage(page, `importDatasetToNewProject-${ORGANIZATION_ID}-${WORKSPACE_ID}`)
                ).toHaveLength(1);

                await cancelJobFromJobScheduler(importingJob, page);

                await expect(page.getByLabel('dataset-import-panel')).toBeHidden();
                expect(
                    await getLocalStorage(page, `importDatasetToNewProject-${ORGANIZATION_ID}-${WORKSPACE_ID}`)
                ).toHaveLength(0);
            });

            test('error', async ({ page, registerApiResponse }) => {
                await openImportModal(page);

                registerJobResponses(registerApiResponse, preparingJobId, getMockedPreparingJob, {
                    steps: [mockedStep],
                    metadata: {
                        warnings: [],
                        supported_project_types: supportedProjectTypesSingleTask,
                    },
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                    loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
                ]);

                await expect(
                    page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
                ).toBeVisible();
                await waitForJobToFinish(page, preparingJobId);

                await fillProjectNameAndType(page, projectName, new RegExp(project_type, 'i'));
                await clickNext(page);

                const mockedImportingFailedStep = {
                    index: 1,
                    progress: 100,
                    state: JobStepState.FAILED,
                    step_name: 'Create project from import dataset',
                    message: 'Something went wrong. Please try again',
                };

                registerJobResponses(registerApiResponse, importingJobId, getMockedImportingJob, {
                    steps: [mockedImportingFailedStep],
                    state: JobState.FAILED,
                    metadata: {},
                });

                await Promise.all([
                    page.waitForRequest(async (res) => res.url().includes(`/jobs/${importingJobId}`)),
                    clickCreate(page),
                ]);

                await expect(
                    page.getByText(`${mockedImportingFailedStep.step_name}: ${mockedImportingFailedStep.message}`)
                ).toBeVisible();
                await waitForJobToFinish(page, importingJobId, JobState.FAILED);

                await expect(page.getByText(`Import dataset - ${fileName} (${fileSize} B)`)).toBeVisible();
                await expect(page.getByText(`Project creation error`)).toBeVisible();
                await expect(page.getByText('Something went wrong. Please try again')).toBeVisible();
            });
        });
    });

    test.describe('TASK CHAIN -> labels step', () => {
        test.beforeEach(async ({ registerApiResponse, page }) => {
            registerApiResponse(
                'GetAllProjectsInAWorkspace',
                (
                    _: OpenApiRequest<'GetAllProjectsInAWorkspace'>,
                    res: ResponseComposition<Record<string, unknown>>,
                    ctx: RestContext
                ) => res(ctx.json(projects))
            );

            registerApiResponse(
                'CreateTusDatasetUpload',
                async (
                    req: OpenApiRequest<'CreateTusDatasetUpload'>,
                    res: ResponseComposition<Record<string, unknown>>,
                    ctx: RestContext
                ): Promise<MockedResponse> =>
                    res(ctx.status(200), ctx.set('Location', `http://localhost:3000/api/v1${req.path}/${uploadId}`))
            );

            registerApiResponse(
                'PrepareDatasetForImport',
                (
                    _: OpenApiRequest<'PrepareDatasetForImport'>,
                    res: ResponseComposition<Record<string, unknown>>,
                    ctx: RestContext
                ) => res(ctx.json({ supported_project_types: supportedProjectTypesTaskChained, warnings: [] }))
            );

            registerApiResponse('TusDatasetUploadHead', setTusProgress(fileSize, fileSize));

            registerApiResponse('PrepareDatasetForImport', (_, res, ctx) => res(ctx.json({ job_id: preparingJobId })));
            registerApiResponse('ImportProjectFromDataset', (_, res, ctx) => res(ctx.json({ job_id: importingJobId })));

            await page.goto('/');
        });

        test('should properly show label group texts in task chain project', async ({ page, registerApiResponse }) => {
            await openImportModal(page);

            registerJobResponses(registerApiResponse, preparingJobId, getMockedPreparingJob, {
                steps: [mockedStep],
                metadata: {
                    supported_project_types: supportedProjectTypesTaskChained,
                },
            });

            await Promise.all([
                page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}`)),
                loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
            ]);

            await expect(
                page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
            ).toBeVisible();
            await waitForJobToFinish(page, preparingJobId);

            await fillProjectNameAndType(page, projectName, 'Detection > Segmentation');

            await clickNext(page);

            await expect(getSegmentationGroupLabel(page)).toBeVisible();
            await expect(getDetectionGroupLabel(page)).toBeVisible();
        });
    });
});
