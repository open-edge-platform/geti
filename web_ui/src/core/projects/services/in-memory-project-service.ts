// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceIdentifier } from '../../../../packages/core/src/workspaces/services/workspaces.interface';
import { getMockedLabel, labels as mockedLabels } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../test-utils/mocked-items-factory/mocked-project';
import {
    ExportDatasetStatusDTO,
    ExportStatusStateDTO,
} from '../../configurable-parameters/dtos/configurable-parameters.interface';
import { JobState, JobStepState, JobType } from '../../jobs/jobs.const';
import { JobExportStatus, JobStatusIdentifier } from '../../jobs/jobs.interface';
import { DOMAIN, ProjectIdentifier } from '../core.interface';
import {
    CreateDatasetBody,
    CreateDatasetResponse,
    Dataset,
    DatasetIdentifier,
    DeleteDatasetResponse,
    ExportDatasetIdentifier,
    ExportDatasetStatusIdentifier,
} from '../dataset.interface';
import { ProjectStatus } from '../project-status.interface';
import {
    CreateProjectProps,
    ProjectExport,
    ProjectExportIdentifier,
    ProjectImport,
    ProjectImportIdentifier,
    ProjectImportStatus,
    ProjectName,
    ProjectProps,
} from '../project.interface';
import { PerformanceType, TaskMetadata } from '../task.interface';
import { ImportOptions, ProjectService } from './project-service.interface';

const inMemoryDatasets = [
    {
        id: 'in-memory-dataset',
        name: 'In memory dataset',
        useForTraining: true,
        creationTime: '2022-07-22T20:09:22.576000+00:00',
    },
];

export const createInMemoryProjectService = (): ProjectService => {
    const editProject = async (_projectIdentifier: ProjectIdentifier, project: ProjectProps): Promise<ProjectProps> => {
        return project;
    };

    const createProject = async (
        _workspaceIdentifier: WorkspaceIdentifier,
        name: string,
        domains: DOMAIN[],
        _tasksLabels: TaskMetadata[]
    ): Promise<CreateProjectProps> => {
        return getMockedProject({
            id: '1',
            name,
            domains,
            creationDate: new Date(),
            labels: [],
            thumbnail: '',
            tasks: [],
        });
    };

    const deleteProject = async (_projectIdentifier: ProjectIdentifier): Promise<string> => {
        return 'success';
    };

    const getProjects: ProjectService['getProjects'] = async (_workspaceIdentifier: WorkspaceIdentifier) => {
        const projects = [
            getMockedProject({
                id: 'test-project1',
                name: 'Test project 1',
                creationDate: new Date('2021-07-08'),
                domains: [DOMAIN.DETECTION],
                labels: [
                    getMockedLabel({ id: 'test', name: 'test' }),
                    getMockedLabel({ id: 'empty', name: 'Empty Detection task label', isExclusive: true }),
                ],
                thumbnail: 'v2/test-project1/thumbnail',
                tasks: [],
                datasets: inMemoryDatasets,
            }),
            getMockedProject({
                id: 'animal-project',
                name: 'Animal project',
                creationDate: new Date('2020-12-10'),
                domains: [DOMAIN.DETECTION],
                labels: [
                    getMockedLabel({ id: 'dog', name: 'dog', color: '#aadd55' }),
                    getMockedLabel({ id: 'cat', name: 'cat', color: '#3399ff' }),
                ],
                thumbnail: 'v2/animal-project/thumbnail',
                tasks: [],
                datasets: inMemoryDatasets,
            }),
            getMockedProject({
                id: 'test-project2',
                name: 'Test project 2',
                creationDate: new Date('2021-07-09'),
                domains: [DOMAIN.SEGMENTATION],
                labels: [
                    getMockedLabel({ id: 'test_label', name: 'test_label', color: '#00bbff' }),
                    getMockedLabel({ id: 'test_label2', name: 'test_label2', color: '#dddd00' }),
                    getMockedLabel({ id: 'test_label3', name: 'test_label3', color: '#ffccdd' }),
                    getMockedLabel({
                        id: 'empty',
                        name: 'Empty Segmentation task label',
                        color: '#dd0000',
                        isExclusive: true,
                    }),
                ],
                thumbnail: 'v2/test-project2/thumbnail',
                tasks: [],
                datasets: inMemoryDatasets,
            }),
            getMockedProject({
                id: 'test-project3',
                name: 'Test project 3',
                creationDate: new Date('2021-05-10'),
                domains: [DOMAIN.CLASSIFICATION],
                labels: [
                    getMockedLabel({ id: 'test_label', name: 'test_label', color: '#bbddbb' }),
                    getMockedLabel({ id: 'test_label2', name: 'test_label2', color: '#00aa00' }),
                    getMockedLabel({ id: 'test_label3', name: 'test_label3', color: '#ffffdd' }),
                    getMockedLabel({
                        id: 'empty',
                        name: 'Empty Classification task label',
                        color: '#00ddff',
                        isExclusive: true,
                    }),
                ],
                thumbnail: 'v2/test-project3/thumbnail',
                tasks: [],
                datasets: inMemoryDatasets,
                storageInfo: {},
            }),
        ];

        return { projects, nextPage: null };
    };

    const getProjectNames = async (
        _workspaceIdentifier: WorkspaceIdentifier
    ): Promise<{ projects: ProjectName[] }> => ({
        projects: [
            {
                name: 'Project name 1',
                id: 'project-id-1',
            },
            {
                name: 'Project name 2',
                id: 'project-id-2',
            },
        ],
    });

    const getProject = async (projectIdentifier: ProjectIdentifier): Promise<ProjectProps> => {
        if (projectIdentifier.projectId === 'project-task-chain-id') {
            const [detectionLabel, ...classificationlabels] = mockedLabels;

            return getMockedProject({
                id: projectIdentifier.projectId,
                name: 'In memory detection - classification',
                domains: [DOMAIN.DETECTION, DOMAIN.CLASSIFICATION],
                labels: mockedLabels,
                creationDate: new Date(),
                thumbnail: '',
                tasks: [
                    {
                        id: '1',
                        labels: [detectionLabel],
                        domain: DOMAIN.DETECTION,
                        title: 'Detection',
                    },
                    {
                        id: '2',
                        labels: classificationlabels,
                        domain: DOMAIN.CLASSIFICATION,
                        title: 'Classification',
                    },
                ],
                datasets: inMemoryDatasets,
            });
        } else if (projectIdentifier.projectId === 'test-classification') {
            return getMockedProject({
                id: projectIdentifier.projectId,
                name: 'In memory classification',
                domains: [DOMAIN.CLASSIFICATION],
                labels: mockedLabels,
                creationDate: new Date(),
                thumbnail: '',
                tasks: [
                    {
                        id: '1',
                        labels: mockedLabels,
                        domain: DOMAIN.CLASSIFICATION,
                        title: 'Classification',
                    },
                ],
                datasets: inMemoryDatasets,
            });
        }

        return getMockedProject({
            id: projectIdentifier.projectId,
            name: 'In memory segmentation',
            domains: [DOMAIN.SEGMENTATION],
            labels: mockedLabels,
            creationDate: new Date(),
            thumbnail: '',
            tasks: [
                {
                    id: '1',
                    labels: mockedLabels,
                    domain: DOMAIN.SEGMENTATION,
                    title: 'Segmentation',
                },
            ],
            datasets: inMemoryDatasets,
        });
    };

    const getProjectStatus = async ({ projectId }: ProjectIdentifier): Promise<ProjectStatus> => {
        switch (projectId) {
            case 'animal-project':
                return {
                    performance: {
                        type: PerformanceType.DEFAULT,
                        score: 0.34,
                        taskPerformances: [
                            {
                                taskNodeId: 'task-id',
                                score: {
                                    value: 0.34,
                                    metricType: 'accuracy',
                                },
                            },
                        ],
                    },
                    isTraining: true,
                    trainingDetails: {
                        progress: '4%',
                        timeRemaining: '01:09',
                    },
                    tasks: [],
                };
            case 'test-project1':
                return {
                    performance: {
                        type: PerformanceType.DEFAULT,
                        score: 0,
                        taskPerformances: [
                            {
                                taskNodeId: 'task-id',
                                score: {
                                    value: 0,
                                    metricType: 'accuracy',
                                },
                            },
                        ],
                    },
                    isTraining: true,
                    trainingDetails: {
                        progress: '64%',
                        timeRemaining: '01:00:06',
                    },
                    tasks: [],
                };

            case 'test-project2':
                return {
                    performance: {
                        type: PerformanceType.DEFAULT,
                        score: 0.95,
                        taskPerformances: [
                            {
                                taskNodeId: 'task-id',
                                score: {
                                    value: 0.95,
                                    metricType: 'accuracy',
                                },
                            },
                        ],
                    },
                    isTraining: false,
                    tasks: [],
                };
            default:
                return {
                    performance: {
                        type: PerformanceType.DEFAULT,
                        score: 0.2,
                        taskPerformances: [
                            {
                                taskNodeId: 'task-id',
                                score: {
                                    value: 0.2,
                                    metricType: 'accuracy',
                                },
                            },
                        ],
                    },
                    isTraining: true,
                    trainingDetails: {
                        progress: '7%',
                        timeRemaining: '01:00:06',
                    },
                    tasks: [],
                };
        }
    };

    const prepareExportDatasetJob = async (_datasetIdentifier: ExportDatasetIdentifier): Promise<{ jobId: string }> => {
        return {
            jobId: '123123',
        };
    };

    const exportDatasetStatus = async (
        _datasetIdentifier: ExportDatasetStatusIdentifier
    ): Promise<ExportDatasetStatusDTO> => {
        return {
            message: 'test',
            progress: -1,
            state: ExportStatusStateDTO.DONE,
            download_url: 'test_url',
        };
    };

    const exportDatasetStatusJob = async (_datasetIdentifier: JobStatusIdentifier): Promise<JobExportStatus> => {
        return {
            id: '6513c1c81b63044e0b08afe5',
            type: JobType.EXPORT_DATASET,
            creationTime: '2023-09-27T05:46:48.655000+00:00',
            startTime: null,
            endTime: null,
            name: 'Dataset Export',
            authorId: 'admin@intel.com',
            state: JobState.SCHEDULED,
            steps: [
                {
                    message: null,
                    index: 1,
                    progress: -1,
                    state: JobStepState.RUNNING,
                    stepName: 'Create export dataset',
                },
            ],
            cancellationInfo: {
                isCancelled: false,
                userUId: null,
                cancelTime: null,
                isCancellable: true,
            },
            metadata: { project: { id: 'some-id', name: 'some-name' } },
        };
    };

    const createDataset = async (_createDatasetBody: CreateDatasetBody): Promise<CreateDatasetResponse> => {
        return {
            id: '1234',
            name: 'testing dataset',
            useForTraining: false,
            creationTime: '2022-07-22T20:09:22.576000+00:00',
        };
    };

    const deleteDataset = async (_datasetIdentifier: DatasetIdentifier): Promise<DeleteDatasetResponse> => {
        return {
            result: 'ok',
        };
    };

    const exportProject = async (_datasetIdentifier: DatasetIdentifier): Promise<ProjectExport> => {
        return {
            exportProjectId: '62ea1a69f00a19754326589c',
        };
    };

    const exportProjectStatus: ProjectService['exportProjectStatus'] = async (
        _datasetIdentifier: ProjectExportIdentifier
    ) => {
        return {
            id: '670e2278e34f232629cc5d0f',
            type: JobType.EXPORT_PROJECT,
            name: 'Project Export',
            state: JobState.FINISHED,
            steps: [
                {
                    message: 'Project export complete',
                    index: 1,
                    progress: 100,
                    state: JobStepState.FINISHED,
                    duration: 62.033,
                    stepName: 'Exporting project',
                },
            ],
            metadata: {
                downloadUrl:
                    // eslint-disable-next-line max-len
                    'api/v1/organizations/2e0d93df-5ba5-4a83-bfcc-1db631e3eb49/workspaces/416de51f-c19b-4f52-b9c9-b6b0f912dfaf/projects/4f7f233b8d4868886054fa7e/exports/670e22b2506faff2b1b12242/download',
                project: {
                    id: '4f7f233b8d4868886054fa7e',
                    name: 'Fish detection classification',
                },
            },
            authorId: '625d92df-9148-46a8-b588-0ecf358379a3',
            endTime: '2024-10-15T08:07:31.820000+00:00',
            startTime: '2024-10-15T08:06:22.785000+00:00',
            creationTime: '2024-10-15T08:06:16.089000+00:00',
            cancellationInfo: {
                isCancelled: false,
                cancelTime: null,
                userUId: null,
                isCancellable: true,
            },
        };
    };

    const importProject = async (
        _projectImportFileIdentifier: ProjectImportIdentifier,
        _options: ImportOptions
    ): Promise<ProjectImport> => {
        return {
            importProjectId: '62ea1a69f00a19754326589c',
        };
    };

    const getImportProjectStatus = async (
        _datasetIdentifier: ProjectImportIdentifier
    ): Promise<ProjectImportStatus> => {
        return {
            progress: 100,
            projectId: '62e3d0f9562ce1ddf940f1a1',
            state: ExportStatusStateDTO.DONE,
        };
    };

    const updateDataset = async (
        _datasetIdentifier: DatasetIdentifier,
        updatedDataset: Dataset
    ): Promise<CreateDatasetResponse> => {
        return updatedDataset;
    };

    return {
        getProjects,
        getProject,
        getProjectNames,
        editProject,
        createDataset,
        deleteDataset,
        updateDataset,
        createProject,
        deleteProject,
        getProjectStatus,
        prepareExportDatasetJob,
        importProject,
        getImportProjectStatus,
        exportDatasetStatus,
        exportDatasetStatusJob,
        exportProject,
        exportProjectStatus,
    };
};
