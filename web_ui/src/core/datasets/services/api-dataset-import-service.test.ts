// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { rest } from 'msw';

import { apiRequestUrl } from '../../../../packages/core/src/services/test-utils';
import { API_URLS } from '../../../../packages/core/src/services/urls';
import { getMockedDatasetIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { server } from '../../annotations/services/test-utils';
import { DATASET_IMPORT_TASK_TYPE } from '../dataset.enum';
import { DATASET_IMPORT_TASK_TYPE_DTO } from '../dtos/dataset.enum';
import {
    DatasetImportPrepareForNewProjectResponseDTO,
    DatasetPrepareForExistingProjectResponseDTO,
} from '../dtos/dataset.interface';
import { createInMemoryDatasetImportService } from './in-memory-dataset-import-service';
import { getSupportedProjectTypesFromDTO, getWarningsFromDTO } from './utils';

describe('Api dataset import service', () => {
    const mockUploadId = '12345';
    const mockDatasetIdentifier = getMockedDatasetIdentifier();
    const mockWorkspaceIdentifier = {
        workspaceId: mockDatasetIdentifier.workspaceId,
        organizationId: mockDatasetIdentifier.organizationId,
    };
    const mockDatasetData = {
        uploadId: 'upload-id',
        datasetName: 'dataset-name',
    };
    const datasetImportService = createInMemoryDatasetImportService();
    const setAbortController = jest.fn();
    const datasetPrepareImportURL = API_URLS.DATASET.IMPORT_PREPARE(mockWorkspaceIdentifier, mockUploadId);

    it('prepares dataset job', async () => {
        const mockResponse = { jobId: '123' };

        server.use(rest.post(apiRequestUrl(datasetPrepareImportURL), (_req, res, ctx) => res(ctx.json(mockResponse))));
        const response = await datasetImportService.prepareDatasetJob({
            ...mockWorkspaceIdentifier,
            uploadId: mockDatasetData.uploadId,
            setAbortController,
        });

        expect(response).toEqual(mockResponse);
    });

    describe('Dataset import to existing project', () => {
        const { datasetId, ...projectIdentifier } = mockDatasetIdentifier;
        const datasetPrepareImportToExistingURL = API_URLS.DATASET.IMPORT_TO_EXISTING_PROJECT_PREPARE(
            projectIdentifier,
            datasetId
        );

        const datasetImportURL = API_URLS.DATASET.IMPORT_TO_EXISTING_PROJECT(projectIdentifier);

        it('prepares import dataset', async () => {
            const mockResponse: DatasetPrepareForExistingProjectResponseDTO = {
                warnings: [],
                labels: [],
            };

            server.use(
                rest.post(apiRequestUrl(datasetPrepareImportToExistingURL), (_req, res, ctx) =>
                    res(ctx.json(mockResponse))
                )
            );

            const response = await datasetImportService.prepareDatasetToExistingProject({
                ...mockWorkspaceIdentifier,
                projectId: mockDatasetIdentifier.projectId,
                uploadId: mockDatasetData.uploadId,
                setAbortController,
            });

            expect(response).toEqual(mockResponse);
        });

        it('prepares import dataset job', async () => {
            const mockResponse = { jobId: '321' };

            server.use(
                rest.post(apiRequestUrl(datasetPrepareImportToExistingURL), (_req, res, ctx) =>
                    res(ctx.json(mockResponse))
                )
            );
            const response = await datasetImportService.prepareDatasetToExistingProjectJob({
                ...mockWorkspaceIdentifier,
                projectId: mockDatasetIdentifier.projectId,
                uploadId: mockDatasetData.uploadId,
                setAbortController,
            });

            expect(response).toEqual(mockResponse);
        });

        it('imports dataset', async () => {
            server.use(rest.post(apiRequestUrl(datasetImportURL), (_req, res, ctx) => res(ctx.status(200))));

            await datasetImportService.importDatasetToExistingProject({
                ...mockWorkspaceIdentifier,
                projectId: mockDatasetIdentifier.projectId,
                uploadId: mockDatasetData.uploadId,
                datasetId: mockDatasetIdentifier.datasetId,
                datasetName: mockDatasetData.datasetName,
                labelsMap: {},
                setAbortController,
            });
        });

        it('imports dataset job', async () => {
            server.use(rest.post(apiRequestUrl(datasetImportURL), (_req, res, ctx) => res(ctx.status(200))));

            const response = await datasetImportService.importDatasetToExistingProjectJob({
                ...mockWorkspaceIdentifier,
                projectId: mockDatasetIdentifier.projectId,
                uploadId: mockDatasetData.uploadId,
                datasetId: mockDatasetIdentifier.datasetId,
                datasetName: mockDatasetData.datasetName,
                labelsMap: {},
                setAbortController,
            });

            expect(response).toEqual({ jobId: '321' });
        });
    });

    describe('Dataset import and create project', () => {
        const datasetImportURL = API_URLS.DATASET.IMPORT_CREATE(mockWorkspaceIdentifier);

        it('prepares import dataset before creating', async () => {
            const mockResponse: DatasetImportPrepareForNewProjectResponseDTO = {
                warnings: [],
                supported_project_types: [
                    {
                        project_type: 'segmentation',
                        pipeline: {
                            connections: [
                                {
                                    from: 'dataset_0',
                                    to: 'detection_1',
                                },
                            ],
                            tasks: [
                                {
                                    title: 'dataset_0',
                                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.DATASET,
                                    labels: [],
                                },
                                {
                                    title: 'detection_1',
                                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.DETECTION,
                                    labels: [
                                        {
                                            name: 'det',
                                            group: 'Detection labels',
                                        },
                                    ],
                                },
                            ],
                        },
                    },
                ],
            };

            server.use(
                rest.post(apiRequestUrl(datasetPrepareImportURL), (_req, res, ctx) => res(ctx.json(mockResponse)))
            );

            const response = await datasetImportService.prepareDatasetForNewProject({
                ...mockWorkspaceIdentifier,
                uploadId: mockUploadId,
                setAbortController,
            });

            expect(response).toEqual({
                warnings: getWarningsFromDTO(mockResponse.warnings),
                supportedProjectTypes: getSupportedProjectTypesFromDTO(mockResponse.supported_project_types),
            });
        });

        it('imports dataset', async () => {
            server.use(rest.post(apiRequestUrl(datasetImportURL), (_req, res, ctx) => res(ctx.status(200))));

            const response = await datasetImportService.importDatasetToNewProject({
                ...mockWorkspaceIdentifier,
                projectData: {
                    uploadId: mockDatasetData.uploadId,
                    projectName: 'new project name',
                    taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                    labels: [{ name: 'label name', color: '#fff' }],
                },
                setAbortController,
                anomalyRevamp: false,
            });

            expect(response).toEqual({ projectId: '' });
        });

        it('imports dataset job', async () => {
            server.use(rest.post(apiRequestUrl(datasetImportURL), (_req, res, ctx) => res(ctx.status(200))));

            const response = await datasetImportService.importDatasetToNewProjectJob({
                ...mockWorkspaceIdentifier,
                projectData: {
                    uploadId: mockDatasetData.uploadId,
                    projectName: 'new project name',
                    taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                    labels: [{ name: 'label name', color: '#fff' }],
                },
                setAbortController,
                anomalyRevamp: false,
            });

            expect(response).toEqual({ jobId: '321' });
        });
    });
});
