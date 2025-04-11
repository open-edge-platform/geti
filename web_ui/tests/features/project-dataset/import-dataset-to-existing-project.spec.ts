// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect, Page } from '@playwright/test';

import { JobState, JobStepState } from '../../../src/core/jobs/jobs.const';
import { DatasetTabActions } from '../../../src/pages/project-details/components/project-dataset/utils';
import { test } from '../../fixtures/base-test';
import { registerJobList, setTusProgress } from '../../utils/api';
import { loadFile } from '../../utils/dom';
import { cancelJobFromJobScheduler } from '../job-scheduler/utils';
import { projects } from './mocks';
import {
    getLocalStorage,
    getMockedExistingProjectImportingJob,
    getMockedExistingProjectPreparingJob,
    getMockedImportingJob,
    registerJobResponses,
    waitForJobToFinish,
} from './utils';

const WORKSPACE_ID = '61011e42d891c82e13ec92da';
const ORGANIZATION_ID = '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633';
const PROJECT_ID = '61012cdb1d38a5e71ef3baf9';
const PROJECT_URL = `/organizations/${ORGANIZATION_ID}/workspaces/${WORKSPACE_ID}/projects/${PROJECT_ID}`;

const clickUpload = async (page: Page) => {
    return page.getByRole('button', { name: /upload/i }).click();
};

const clickImport = async (page: Page) => {
    return page.getByRole('button', { name: /import/i }).click();
};

const hideImportModal = async (page: Page) => {
    return page.getByRole('button', { name: /hide/i }).click();
};

test.describe('Import dataset to existing project', () => {
    const labels = ['cat', 'dog'];
    const uploadId = '123-321-213';
    const fileName = 'dataset.zip';
    const fileSize = 256;
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

    const preparingJobId = '651bd77c1b63044e0b08b140a';
    const importingJobId = '651bd77c1b63044e0b08b140b';
    const currentDataset = {
        id: '6101254defba22ca453f11cc',
        name: 'Dataset',
        creation_time: '2022-10-24T11:21:50.030000+00:00',
        use_for_training: true,
    };

    test.beforeEach(async ({ registerApiResponse, page }) => {
        registerApiResponse('TusDatasetUploadHead', setTusProgress(fileSize, fileSize));
        registerApiResponse('CreateTusDatasetUpload', async (req, res, ctx) =>
            res(ctx.status(200), ctx.set('Location', `http://localhost:3000/api/v1${req.path}/${uploadId}`))
        );

        registerApiResponse('GetAllProjectsInAWorkspace', (_, res, ctx) => res(ctx.json(projects)));

        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            const project = projects.projects[0];
            return res(
                ctx.json({
                    ...project,
                    pipeline: {
                        ...project.pipeline,
                        tasks: [
                            {
                                id: '6101254defba22ca453f11d8',
                                task_type: 'detection',
                                title: 'Sample detection task',
                                label_schema_id: '6101254defba22ca453f11c8',
                                labels: [
                                    {
                                        color: '#0015ffff',
                                        group: 'default',
                                        hotkey: 'ctrl+1',
                                        id: '6101254defba22ca453f11c1',
                                        is_empty: false,
                                        is_anomalous: false,
                                        name: labels[0],
                                    },
                                    {
                                        color: '#00ffffff',
                                        group: 'default',
                                        hotkey: 'ctrl+2',
                                        id: '6101254defba22ca453f11c2',
                                        is_empty: false,
                                        is_anomalous: false,
                                        name: labels[1],
                                    },
                                ],
                            },
                        ],
                    },
                })
            );
        });

        registerApiResponse('PrepareDatasetForImportToProject', (_, res, ctx) =>
            res(ctx.json({ labels, warnings: [], job_id: preparingJobId }))
        );

        registerApiResponse('ImportDatasetToProject', (_, res, ctx) => res(ctx.json({ job_id: importingJobId })));

        await page.goto(PROJECT_URL);
    });

    test.describe('import successful', (): void => {
        test('no warnings and with empty labels map', async ({ page, registerApiResponse, datasetPage }) => {
            await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

            await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

            registerJobResponses(registerApiResponse, preparingJobId, getMockedExistingProjectPreparingJob, {
                steps: [mockedStep],
                metadata: {
                    warnings: [],
                    labels: [],
                },
            });

            await expect(
                page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
            ).toBeVisible();
            await waitForJobToFinish(page, preparingJobId);

            await expect(
                page.getByText('No labels were detected in the dataset. Only images will be imported.')
            ).toBeVisible();

            registerJobResponses(registerApiResponse, importingJobId, getMockedExistingProjectImportingJob, {
                steps: [mockedImportingStep],
                metadata: {
                    dataset: currentDataset,
                },
            });

            await clickImport(page);

            await expect(
                page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
            ).toBeVisible();

            await waitForJobToFinish(page, importingJobId);
            await expect(
                page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
            ).toBeHidden();
        });

        test('with label mapping', async ({ page, registerApiResponse, datasetPage }) => {
            await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

            await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

            registerJobResponses(registerApiResponse, preparingJobId, getMockedExistingProjectPreparingJob, {
                steps: [mockedStep],
                metadata: {
                    warnings: [],
                    labels: [labels[0], labels[1]],
                },
            });

            await expect(
                page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
            ).toBeVisible();
            await waitForJobToFinish(page, preparingJobId);

            registerJobResponses(registerApiResponse, importingJobId, getMockedExistingProjectImportingJob, {
                steps: [mockedImportingStep],
                metadata: {
                    dataset: currentDataset,
                },
            });

            await clickImport(page);

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
        test('cancel', async ({ page, registerApiResponse, datasetPage }): Promise<void> => {
            await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

            await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

            registerJobResponses(registerApiResponse, preparingJobId, getMockedExistingProjectPreparingJob, {
                steps: [mockedStep],
                metadata: {
                    warnings: [],
                    labels: [],
                },
            });

            await expect(
                page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
            ).toBeVisible();
            expect(
                await getLocalStorage(
                    page,
                    `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                )
            ).toHaveLength(1);

            await Promise.all([
                page.waitForRequest(async (res) => res.url().includes(`/jobs/${preparingJobId}:cancel`)),
                page.getByRole('button', { name: 'Cancel' }).click(),
            ]);

            await expect(page.getByText('Dataset - Import')).toBeHidden();
            await expect(page.getByLabel('dataset-import-panel')).toBeHidden();
            expect(
                await getLocalStorage(
                    page,
                    `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                )
            ).toHaveLength(0);
        });

        test('cancel import from job list', async ({ page, registerApiResponse, datasetPage }): Promise<void> => {
            const preparingJob = getMockedExistingProjectPreparingJob({
                id: preparingJobId,
                name: 'Test preparing importing',
                state: JobState.SCHEDULED,
            });

            registerJobList(registerApiResponse, preparingJob);

            await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

            await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

            await hideImportModal(page);

            expect(
                await getLocalStorage(
                    page,
                    `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                )
            ).toHaveLength(1);
            await expect(page.getByLabel('dataset-import-panel')).toBeVisible();

            await cancelJobFromJobScheduler(preparingJob, page);

            await expect(page.getByLabel('dataset-import-panel')).toBeHidden();
            expect(
                await getLocalStorage(
                    page,
                    `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                )
            ).toHaveLength(0);
        });

        test('error', async ({ page, registerApiResponse, datasetPage }): Promise<void> => {
            await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

            await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

            registerJobResponses(registerApiResponse, preparingJobId, getMockedExistingProjectPreparingJob, {
                state: JobState.FAILED,
                metadata: {
                    warnings: [],
                    labels: [],
                },
            });

            await waitForJobToFinish(page, preparingJobId, JobState.FAILED);

            await expect(page.getByText('Dataset has not been prepared')).toBeVisible();
            await expect(page.getByText('Something went wrong. Please try again')).toBeVisible();

            await page.reload();

            await expect(page.getByText('Preparing error')).toBeVisible();

            await Promise.all([
                page.waitForRequest((res) => res.url().includes(`/jobs/${preparingJobId}`)),
                page.getByRole('button', { name: 'Try again' }).click(),
            ]);
        });
    });

    test.describe('importing job status', (): void => {
        test('cancel', async ({ page, registerApiResponse, datasetPage }): Promise<void> => {
            await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

            await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

            registerJobResponses(registerApiResponse, preparingJobId, getMockedExistingProjectPreparingJob, {
                steps: [mockedStep],
                metadata: {
                    warnings: [],
                    labels: [],
                },
            });

            await expect(
                page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
            ).toBeVisible();
            expect(
                await getLocalStorage(
                    page,
                    `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                )
            ).toHaveLength(1);
            await waitForJobToFinish(page, preparingJobId);

            await expect(
                page.getByText('No labels were detected in the dataset. Only images will be imported.')
            ).toBeVisible();

            registerJobResponses(registerApiResponse, importingJobId, getMockedExistingProjectImportingJob, {
                metadata: {
                    dataset: currentDataset,
                },
            });

            await clickImport(page);

            await expect(page.getByText('Importing...')).toBeVisible();
            await page.getByRole('button', { name: 'dataset-import-menu' }).click();

            await Promise.all([
                page.waitForRequest(async (res) => res.url().includes(`/jobs/${importingJobId}:cancel`)),
                page.getByRole('menuitem', { name: /cancel/i }).click(),
            ]);

            await expect(page.getByText('Dataset - Import')).toBeHidden();
            await expect(page.getByLabel('dataset-import-panel')).toBeHidden();
            expect(
                await getLocalStorage(
                    page,
                    `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                )
            ).toHaveLength(0);
        });

        test('cancel import from job list', async ({ page, registerApiResponse, datasetPage }): Promise<void> => {
            const preparingJob = getMockedExistingProjectPreparingJob({
                id: preparingJobId,
                name: 'Test preparing dataset',
                state: JobState.FINISHED,
                metadata: {
                    warnings: [],
                    labels: [],
                },
            });

            const importingJob = getMockedImportingJob({
                id: importingJobId,
                name: 'Test importing dataset',
                state: JobState.SCHEDULED,
                steps: [mockedImportingStep],
            });

            registerJobList(registerApiResponse, preparingJob);

            await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

            await Promise.all([
                waitForJobToFinish(page, preparingJob.id),
                loadFile(page, clickUpload(page), { name: fileName, size: fileSize }),
            ]);

            registerJobList(registerApiResponse, importingJob);

            await clickImport(page);

            await expect(
                page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
            ).toBeVisible();
            await expect(page.getByLabel('dataset-import-panel')).toBeVisible();
            expect(
                await getLocalStorage(
                    page,
                    `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                )
            ).toHaveLength(1);

            await cancelJobFromJobScheduler(importingJob, page);

            await expect(page.getByLabel('dataset-import-panel')).toBeHidden();
            expect(
                await getLocalStorage(
                    page,
                    `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                )
            ).toHaveLength(0);
        });

        test('error', async ({ page, registerApiResponse, datasetPage }): Promise<void> => {
            await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

            await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

            registerJobResponses(registerApiResponse, preparingJobId, getMockedExistingProjectPreparingJob, {
                steps: [mockedStep],
                metadata: {
                    warnings: [],
                    labels: [],
                },
            });

            await expect(
                page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
            ).toBeVisible();
            await waitForJobToFinish(page, preparingJobId);

            await expect(
                page.getByText('No labels were detected in the dataset. Only images will be imported.')
            ).toBeVisible();

            const mockedImportingFailedStep = {
                index: 1,
                progress: 100,
                state: JobStepState.FAILED,
                step_name: 'Create project from import dataset',
                message: 'Something went wrong. Please try again',
            };

            registerJobResponses(registerApiResponse, importingJobId, getMockedExistingProjectImportingJob, {
                steps: [mockedImportingFailedStep],
                state: JobState.FAILED,
                metadata: {},
            });

            await clickImport(page);

            await expect(
                page.getByText(`${mockedImportingFailedStep.step_name}: ${mockedImportingFailedStep.message}`)
            ).toBeVisible();

            await waitForJobToFinish(page, importingJobId, JobState.FAILED);
            await expect(page.getByText(`Importing error`)).toBeVisible();
            await expect(page.getByText('Something went wrong. Please try again')).toBeVisible();
        });

        test(
            'should be visible after page reload',
            {
                annotation: {
                    type: 'issue',
                },
            },
            async ({ page, registerApiResponse, datasetPage }) => {
                await datasetPage.selectDatasetTabMenuItem(currentDataset.name, DatasetTabActions.ImportDataset);

                await loadFile(page, clickUpload(page), { name: fileName, size: fileSize });

                registerJobResponses(registerApiResponse, preparingJobId, getMockedExistingProjectPreparingJob, {
                    steps: [mockedStep],
                    metadata: {
                        warnings: [],
                        labels: [],
                    },
                });

                await expect(
                    page.getByRole('dialog').getByText(`${mockedStep.step_name}: ${mockedStep.message}`)
                ).toBeVisible();
                expect(
                    await getLocalStorage(
                        page,
                        `importDatasetToExistingProject-${ORGANIZATION_ID}-${WORKSPACE_ID}-${PROJECT_ID}`
                    )
                ).toHaveLength(1);
                await waitForJobToFinish(page, preparingJobId);

                registerJobResponses(registerApiResponse, importingJobId, getMockedExistingProjectImportingJob, {
                    steps: [mockedImportingStep],
                    metadata: {
                        dataset: currentDataset,
                    },
                });

                await clickImport(page);

                await expect(
                    page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
                ).toBeVisible();

                await page.reload();

                await expect(
                    page.getByText(`${mockedImportingStep.step_name}: ${mockedImportingStep.message}`)
                ).toBeVisible();
            }
        );
    });
});
