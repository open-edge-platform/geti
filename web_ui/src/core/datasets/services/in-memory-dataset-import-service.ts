// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/* eslint-disable @typescript-eslint/no-unused-vars */

import { WorkspaceIdentifier } from '../../../../packages/core/src/workspaces/services/workspaces.interface';
import { JobState, JobType } from '../../jobs/jobs.const';
import {
    JobImportDatasetToExistingProjectStatus,
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
    JobPrepareDatasetToExistingProjectStatus,
    JobStatusIdentifier,
} from '../../jobs/jobs.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { CreateDatasetResponse } from '../../projects/dataset.interface';
import { DATASET_IMPORT_TASK_TYPE } from '../dataset.enum';
import {
    DatasetImportIdentifier,
    DatasetImportPrepareForNewProjectResponse,
    DatasetImportToNewProjectIdentifier,
    DatasetImportToNewProjectResponse,
    DatasetPrepareForExistingProjectResponse,
} from '../dataset.interface';
import { DatasetImportService } from './dataset.interface';

export const createInMemoryDatasetImportService = (): DatasetImportService => {
    const prepareDatasetForNewProject = async (
        _data: DatasetImportIdentifier
    ): Promise<DatasetImportPrepareForNewProjectResponse> => {
        return Promise.resolve({
            warnings: [],
            supportedProjectTypes: [
                {
                    projectType: 'segmentation',
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
                                taskType: DATASET_IMPORT_TASK_TYPE.DATASET,
                                labels: [],
                            },
                            {
                                title: 'detection_1',
                                taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
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
        });
    };

    const prepareDatasetJob = async (_data: DatasetImportIdentifier): Promise<{ jobId: string }> => {
        return Promise.resolve({ jobId: '123' });
    };

    const importDatasetToNewProject = async (
        _data: DatasetImportToNewProjectIdentifier
    ): Promise<DatasetImportToNewProjectResponse> => {
        return Promise.resolve({ projectId: '' });
    };

    const importDatasetToNewProjectJob = async (
        _data: DatasetImportToNewProjectIdentifier
    ): Promise<{ jobId: string }> => {
        return Promise.resolve({ jobId: '321' });
    };

    const prepareDatasetToExistingProject = async (
        _datasetIdentifier: DatasetImportIdentifier
    ): Promise<DatasetPrepareForExistingProjectResponse> => {
        return Promise.resolve({ warnings: [], labels: [] });
    };
    const prepareDatasetToExistingProjectJob = async (
        _datasetIdentifier: DatasetImportIdentifier
    ): Promise<{ jobId: string }> => {
        return Promise.resolve({ jobId: '321' });
    };

    const importDatasetToExistingProject = async (
        _projectIdentifier: ProjectIdentifier
    ): Promise<CreateDatasetResponse> => {
        return Promise.resolve({ id: '', name: '', creationTime: '', useForTraining: true });
    };

    const importDatasetToExistingProjectJob = async (
        _projectIdentifier: ProjectIdentifier
    ): Promise<{ jobId: string }> => {
        return Promise.resolve({ jobId: '321' });
    };

    const prepareDatasetImportNewProjectJob = async (
        _datasetIdentifier: JobStatusIdentifier
    ): Promise<JobPrepareDatasetImportNewProjectStatus> => {
        return {
            id: '6513c1c81b63044e0b08afe5',
            type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT,
            creationTime: '2023-09-27T05:46:48.655000+00:00',
            startTime: null,
            endTime: null,
            name: 'prepare import new project job',
            authorId: 'admin@intel.com',
            state: JobState.SCHEDULED,
            steps: [],
            cancellationInfo: {
                isCancelled: false,
                userUId: null,
                cancelTime: null,
                isCancellable: true,
            },
            metadata: {},
        };
    };

    const importDatasetToNewProjectStatusJob = async (
        _datasetIdentifier: JobStatusIdentifier
    ): Promise<JobImportDatasetToNewProjectStatus> => {
        return {
            id: '6513c1c81b63044e0b08afe5',
            type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT,
            creationTime: '2023-09-27T05:46:48.655000+00:00',
            startTime: null,
            endTime: null,
            name: 'Create and Import to New Project',
            authorId: 'admin@intel.com',
            state: JobState.SCHEDULED,
            steps: [],
            cancellationInfo: {
                isCancelled: false,
                userUId: null,
                cancelTime: null,
                isCancellable: true,
            },
            metadata: {},
        };
    };

    const prepareDatasetToExistingProjectStatusJob = async (
        _datasetIdentifier: JobStatusIdentifier
    ): Promise<JobPrepareDatasetToExistingProjectStatus> => {
        return {
            id: '6513c1c81b63044e0b08afe5',
            type: JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT,
            creationTime: '2023-09-27T05:46:48.655000+00:00',
            startTime: null,
            endTime: null,
            name: 'Create and Import to New Project',
            authorId: 'admin@intel.com',
            state: JobState.SCHEDULED,
            steps: [],
            cancellationInfo: {
                isCancelled: false,
                userUId: null,
                cancelTime: null,
                isCancellable: true,
            },
            metadata: {},
        };
    };

    const importDatasetToExistingProjectStatusJob = async (
        _datasetIdentifier: JobStatusIdentifier
    ): Promise<JobImportDatasetToExistingProjectStatus> => {
        return {
            id: '6513c1c81b63044e0b08afe5',
            type: JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT,
            creationTime: '2023-09-27T05:46:48.655000+00:00',
            startTime: null,
            endTime: null,
            name: 'Create and Import to New Project',
            authorId: 'admin@intel.com',
            state: JobState.SCHEDULED,
            steps: [],
            cancellationInfo: {
                isCancelled: false,
                userUId: null,
                cancelTime: null,
                isCancellable: true,
            },
            metadata: {},
        };
    };

    const deleteImportProjectFromDataset = async (
        workspaceIdentifier: WorkspaceIdentifier & { fileId: string }
    ): Promise<void> => {
        await Promise.resolve();
    };

    return {
        prepareDatasetForNewProject,
        prepareDatasetJob,
        prepareDatasetImportNewProjectJob,
        importDatasetToNewProject,
        importDatasetToNewProjectJob,
        importDatasetToNewProjectStatusJob,

        prepareDatasetToExistingProject,
        prepareDatasetToExistingProjectJob,
        prepareDatasetToExistingProjectStatusJob,

        importDatasetToExistingProject,
        importDatasetToExistingProjectJob,
        importDatasetToExistingProjectStatusJob,

        deleteImportProjectFromDataset,
    };
};
