// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';

import { getMockedDatasetImportPayload } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImportStatusJob, getMockedPrepareJob } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { createInMemoryApiFeatureFlagService } from '../../feature-flags/services/in-memory-api-feature-flag-service';
import { JobState } from '../../jobs/jobs.const';
import {
    JobImportDatasetToExistingProjectStatus,
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
    JobPrepareDatasetToExistingProjectStatus,
} from '../../jobs/jobs.interface';
import { DATASET_IMPORT_TASK_TYPE } from '../dataset.enum';
import { DatasetImportProjectData } from '../dataset.interface';
import { createInMemoryDatasetImportService } from '../services/in-memory-dataset-import-service';
import { useDatasetImportQueries } from './use-dataset-import-queries.hook';

const mockedDatasetImportService = createInMemoryDatasetImportService();
const mockedFeatureFlagService = createInMemoryApiFeatureFlagService();

mockedDatasetImportService.importDatasetToNewProject = jest.fn();
mockedDatasetImportService.prepareDatasetForNewProject = jest.fn();
mockedDatasetImportService.importDatasetToExistingProject = jest.fn();
mockedDatasetImportService.prepareDatasetToExistingProject = jest.fn();
mockedDatasetImportService.prepareDatasetImportNewProjectJob = jest.fn();
mockedDatasetImportService.importDatasetToNewProjectStatusJob = jest.fn();
mockedDatasetImportService.prepareDatasetToExistingProjectStatusJob = jest.fn();
mockedDatasetImportService.importDatasetToExistingProjectStatusJob = jest.fn();

const mockedAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockedAddNotification }),
}));

const projectId = 'project-id';

const mockDatasetImportPayload = getMockedDatasetImportPayload({
    uploadId: 'upload_1',
});

const wrapper = ({ children }: { children: ReactNode }) => {
    return (
        <RequiredProviders
            featureFlagService={mockedFeatureFlagService}
            datasetImportService={mockedDatasetImportService}
        >
            {children}
        </RequiredProviders>
    );
};

const renderDatasetImportQueriesHook = () => {
    return renderHookWithProviders(() => useDatasetImportQueries(), {
        providerProps: {
            featureFlagService: mockedFeatureFlagService,
            datasetImportService: mockedDatasetImportService,
        },
    });
};

describe('useDatasetImportQueries', () => {
    describe('Import dataset and create project', () => {
        beforeEach(() => {
            jest.resetAllMocks();
        });

        it('prepares import before create', async () => {
            const { workspaceId, setAbortController, organizationId } = mockDatasetImportPayload;
            const mockUploadId = '123456';

            const { result } = renderDatasetImportQueriesHook();

            result.current.prepareDatasetForNewProject.mutate({
                organizationId,
                workspaceId,
                uploadId: mockUploadId,
                setAbortController,
            });

            await waitFor(() => {
                expect(mockedDatasetImportService.prepareDatasetForNewProject).toHaveBeenCalledWith({
                    organizationId,
                    workspaceId,
                    uploadId: mockUploadId,
                    setAbortController,
                });
            });
        });

        it('imports dataset and creates project', async () => {
            const { organizationId, workspaceId, setAbortController } = mockDatasetImportPayload;
            const mockProjectData: DatasetImportProjectData = {
                uploadId: '12345',
                projectName: 'example project',
                taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                labels: [],
            };

            const { result } = renderDatasetImportQueriesHook();

            result.current.importDatasetToNewProject.mutate({
                organizationId,
                workspaceId,
                projectData: mockProjectData,
                setAbortController,
                anomalyRevamp: false,
            });

            await waitFor(() => {
                expect(mockedDatasetImportService.importDatasetToNewProject).toHaveBeenCalledWith({
                    organizationId,
                    workspaceId,
                    projectData: mockProjectData,
                    setAbortController,
                    anomalyRevamp: false,
                });
            });
        });

        it('imports dataset error', async () => {
            jest.mocked(mockedDatasetImportService.importDatasetToNewProject).mockRejectedValue('test error');
            const { organizationId, workspaceId, setAbortController } = mockDatasetImportPayload;
            const mockProjectData: DatasetImportProjectData = {
                uploadId: '12345',
                projectName: 'example project',
                taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                labels: [],
            };

            const { result } = renderDatasetImportQueriesHook();

            result.current.importDatasetToNewProject.mutate({
                organizationId,
                workspaceId,
                projectData: mockProjectData,
                setAbortController,
                anomalyRevamp: false,
            });

            await waitFor(() => {
                expect(mockedAddNotification).toHaveBeenCalled();
            });
        });

        describe('interval queries', () => {
            const mockedOnError = jest.fn();
            const mockedOnSuccess = jest.fn();
            const mockedOnSettled = jest.fn();
            const mockedData = { organizationId: '123', workspaceId: '321', jobId: '213' };
            const { result: queriesHooks } = renderHook(() => useDatasetImportQueries(), {
                wrapper,
            });

            beforeEach(() => {
                jest.clearAllMocks();
            });

            it('prepare import job status "FINISHED"', async () => {
                const mockedJobResponse = getMockedPrepareJob({
                    state: JobState.FINISHED,
                }) as JobPrepareDatasetImportNewProjectStatus;
                jest.mocked(mockedDatasetImportService.prepareDatasetImportNewProjectJob).mockResolvedValue(
                    mockedJobResponse
                );

                renderHook(
                    () =>
                        queriesHooks.current.usePreparingStatusJob({
                            data: mockedData,
                            enabled: true,
                            onError: mockedOnError,
                            onSuccess: mockedOnSuccess,
                            onSettled: mockedOnSettled,
                        }),
                    { wrapper }
                );

                await waitFor(() => {
                    expect(mockedDatasetImportService.prepareDatasetImportNewProjectJob).toHaveBeenCalledWith(
                        mockedData
                    );
                    expect(mockedOnError).not.toHaveBeenCalled();
                    expect(mockedOnSuccess).toHaveBeenCalledWith(mockedJobResponse);
                    expect(mockedOnSettled).toHaveBeenCalledWith(mockedJobResponse);
                });
            });

            it('prepare import job status "FAILED"', async () => {
                const mockedJobResponse = getMockedPrepareJob({
                    state: JobState.FAILED,
                }) as JobPrepareDatasetImportNewProjectStatus;
                jest.mocked(mockedDatasetImportService.prepareDatasetImportNewProjectJob).mockResolvedValue(
                    mockedJobResponse
                );

                renderHook(
                    () =>
                        queriesHooks.current.usePreparingStatusJob({
                            data: mockedData,
                            enabled: true,
                            onError: mockedOnError,
                            onSuccess: mockedOnSuccess,
                            onSettled: mockedOnSettled,
                        }),
                    { wrapper }
                );

                await waitFor(() => {
                    expect(mockedOnSuccess).not.toHaveBeenCalled();
                    expect(mockedOnSettled).toHaveBeenCalledWith(mockedJobResponse);
                    expect(mockedDatasetImportService.prepareDatasetImportNewProjectJob).toHaveBeenCalledWith(
                        mockedData
                    );
                    expect(mockedOnError).toHaveBeenCalledWith({
                        message: 'Something went wrong. Please try again',
                        response: { status: 501 },
                    });
                });
            });

            it('import job status "FINISHED"', async () => {
                const mockedJobResponse = getMockedImportStatusJob({
                    state: JobState.FINISHED,
                }) as JobImportDatasetToNewProjectStatus;
                jest.mocked(mockedDatasetImportService.importDatasetToNewProjectStatusJob).mockResolvedValue(
                    mockedJobResponse
                );

                renderHook(
                    () =>
                        queriesHooks.current.useImportingStatusJob({
                            data: mockedData,
                            enabled: true,
                            onError: mockedOnError,
                            onSuccess: mockedOnSuccess,
                        }),
                    { wrapper }
                );

                await waitFor(() => {
                    expect(mockedDatasetImportService.importDatasetToNewProjectStatusJob).toHaveBeenCalledWith(
                        mockedData
                    );
                    expect(mockedOnError).not.toHaveBeenCalled();
                    expect(mockedOnSuccess).toHaveBeenCalledWith(mockedJobResponse);
                });
            });

            it('import job status "FAILED"', async () => {
                const mockedJobResponse = getMockedImportStatusJob({
                    state: JobState.FAILED,
                }) as JobImportDatasetToNewProjectStatus;
                jest.mocked(mockedDatasetImportService.importDatasetToNewProjectStatusJob).mockResolvedValue(
                    mockedJobResponse
                );

                renderHook(
                    () =>
                        queriesHooks.current.useImportingStatusJob({
                            data: mockedData,
                            enabled: true,
                            onError: mockedOnError,
                            onSuccess: mockedOnSuccess,
                        }),
                    { wrapper }
                );

                await waitFor(() => {
                    expect(mockedOnSuccess).not.toHaveBeenCalled();
                    expect(mockedDatasetImportService.importDatasetToNewProjectStatusJob).toHaveBeenCalledWith(
                        mockedData
                    );
                    expect(mockedOnError).toHaveBeenCalledWith({
                        message: 'Something went wrong. Please try again',
                        response: { status: 501 },
                    });
                });
            });
        });
    });

    describe('Import dataset to existing project', () => {
        beforeEach(() => {
            jest.resetAllMocks();
        });

        it('prepares import dataset correctly', async () => {
            const { organizationId, workspaceId, uploadId, setAbortController } = mockDatasetImportPayload;

            const { result } = renderDatasetImportQueriesHook();

            result.current.prepareDatasetToExistingProject.mutate({
                organizationId,
                workspaceId,
                projectId,
                uploadId,
                setAbortController,
            });

            await waitFor(() => {
                expect(mockedDatasetImportService.prepareDatasetToExistingProject).toHaveBeenCalledWith({
                    organizationId,
                    workspaceId,
                    projectId,
                    uploadId,
                    setAbortController,
                });
            });
        });

        it('imports dataset correctly', async () => {
            const { workspaceId, uploadId, setAbortController, organizationId } = mockDatasetImportPayload;

            const { result } = renderDatasetImportQueriesHook();

            result.current.importDatasetToExistingProject.mutate({
                organizationId,
                workspaceId,
                projectId,
                uploadId,
                datasetId: '',
                datasetName: '',
                labelsMap: { 'some-id': 'some-other-id' },
                setAbortController,
            });

            await waitFor(() => {
                expect(mockedDatasetImportService.importDatasetToExistingProject).toHaveBeenCalledWith({
                    organizationId,
                    workspaceId,
                    projectId,
                    uploadId,
                    datasetId: '',
                    datasetName: '',
                    labelsMap: { 'some-id': 'some-other-id' },
                    setAbortController,
                });
            });
        });

        describe('interval queries', () => {
            const mockedOnError = jest.fn();
            const mockedOnSuccess = jest.fn();
            const mockedOnSettled = jest.fn();
            const mockedData = { organizationId: '123', workspaceId: '321', jobId: '213' };
            const { result: queriesHooks } = renderDatasetImportQueriesHook();

            beforeEach(() => {
                jest.clearAllMocks();
            });

            it('prepare import job status "FINISHED"', async () => {
                const mockedJobResponse = getMockedPrepareJob({
                    state: JobState.FINISHED,
                }) as JobPrepareDatasetToExistingProjectStatus;
                jest.mocked(mockedDatasetImportService.prepareDatasetToExistingProjectStatusJob).mockResolvedValue(
                    mockedJobResponse
                );

                renderHook(
                    () =>
                        queriesHooks.current.usePreparingExistingProjectStatusJob({
                            data: mockedData,
                            enabled: true,
                            onError: mockedOnError,
                            onSuccess: mockedOnSuccess,
                            onSettled: mockedOnSettled,
                        }),
                    { wrapper }
                );

                await waitFor(() => {
                    expect(mockedDatasetImportService.prepareDatasetToExistingProjectStatusJob).toHaveBeenCalledWith(
                        mockedData
                    );
                    expect(mockedOnError).not.toHaveBeenCalled();
                    expect(mockedOnSuccess).toHaveBeenCalledWith(mockedJobResponse);
                    expect(mockedOnSettled).toHaveBeenCalledWith(mockedJobResponse);
                });
            });

            it('prepare import job status "FAILED"', async () => {
                const mockedJobResponse = getMockedPrepareJob({
                    state: JobState.FAILED,
                }) as JobPrepareDatasetToExistingProjectStatus;
                jest.mocked(mockedDatasetImportService.prepareDatasetToExistingProjectStatusJob).mockResolvedValue(
                    mockedJobResponse
                );

                renderHook(
                    () =>
                        queriesHooks.current.usePreparingExistingProjectStatusJob({
                            data: mockedData,
                            enabled: true,
                            onError: mockedOnError,
                            onSuccess: mockedOnSuccess,
                            onSettled: mockedOnSettled,
                        }),
                    { wrapper }
                );

                await waitFor(() => {
                    expect(mockedOnSuccess).not.toHaveBeenCalled();
                    expect(mockedOnSettled).toHaveBeenCalledWith(mockedJobResponse);
                    expect(mockedDatasetImportService.prepareDatasetToExistingProjectStatusJob).toHaveBeenCalledWith(
                        mockedData
                    );
                    expect(mockedOnError).toHaveBeenCalledWith({
                        message: 'Something went wrong. Please try again',
                        response: { status: 501 },
                    });
                });
            });
            it('import job status "FINISHED"', async () => {
                const mockedJobResponse = getMockedImportStatusJob({
                    state: JobState.FINISHED,
                }) as JobImportDatasetToExistingProjectStatus;
                jest.mocked(mockedDatasetImportService.importDatasetToExistingProjectStatusJob).mockResolvedValue(
                    mockedJobResponse
                );

                renderHook(
                    () =>
                        queriesHooks.current.useImportingExistingProjectStatusJob({
                            data: mockedData,
                            enabled: true,
                            onError: mockedOnError,
                            onSuccess: mockedOnSuccess,
                        }),
                    { wrapper }
                );

                await waitFor(() => {
                    expect(mockedDatasetImportService.importDatasetToExistingProjectStatusJob).toHaveBeenCalledWith(
                        mockedData
                    );
                    expect(mockedOnError).not.toHaveBeenCalled();
                    expect(mockedOnSuccess).toHaveBeenCalledWith(mockedJobResponse);
                });
            });

            it('import job status "FAILED"', async () => {
                const mockedJobResponse = getMockedImportStatusJob({
                    state: JobState.FAILED,
                }) as JobImportDatasetToExistingProjectStatus;
                jest.mocked(mockedDatasetImportService.importDatasetToExistingProjectStatusJob).mockResolvedValue(
                    mockedJobResponse
                );

                renderHook(
                    () =>
                        queriesHooks.current.useImportingExistingProjectStatusJob({
                            data: mockedData,
                            enabled: true,
                            onError: mockedOnError,
                            onSuccess: mockedOnSuccess,
                        }),
                    { wrapper }
                );

                await waitFor(() => {
                    expect(mockedOnSuccess).not.toHaveBeenCalled();
                    expect(mockedDatasetImportService.importDatasetToExistingProjectStatusJob).toHaveBeenCalledWith(
                        mockedData
                    );
                    expect(mockedOnError).toHaveBeenCalledWith({
                        message: 'Something went wrong. Please try again',
                        response: { status: 501 },
                    });
                });
            });
        });
    });
});
