// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEqual } from 'lodash-es';
import { rest } from 'msw';

import { apiRequestUrl } from '../../../../packages/core/src/services/test-utils';
import { API_URLS } from '../../../../packages/core/src/services/urls';
import { getMockedDatasetIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject, getMockedProjectDTO } from '../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../test-utils/mocked-items-factory/mocked-tasks';
import { server } from '../../annotations/services/test-utils';
import { ExportStatusStateDTO } from '../../configurable-parameters/dtos/configurable-parameters.interface';
import { LABEL_BEHAVIOUR, LabelsRelationType } from '../../labels/label.interface';
import { GROUP_SEPARATOR } from '../../labels/utils';
import { DOMAIN } from '../core.interface';
import { CreateDatasetResponseDTO, DeleteDatasetResponse, ExportFormats } from '../dataset.interface';
import { EditProjectProps, ProjectCreation, ProjectProps } from '../project.interface';
import { createApiProjectService } from './api-project-service';
import { ProjectSortingOptions, ProjectsQueryOptions } from './project-service.interface';
import {
    FLAT_LABELS,
    HIERARCHY_LABELS,
    PROJECT_ANOMALY_CLASSIFICATION,
    PROJECT_ANOMALY_DETECTION,
    PROJECT_ANOMALY_SEGMENTATION,
    PROJECT_CLASSIFICATION,
    PROJECT_DETECTION,
    PROJECT_DETECTION_CLASSIFICATION,
    PROJECT_DETECTION_ORIENTED,
    PROJECT_DETECTION_SEGMENTATION,
    PROJECT_KEYPOINT_DETECTION,
    PROJECT_RESPONSE,
    PROJECT_SEGMENTATION,
    PROJECT_SEGMENTATION_INSTANCE,
} from './test-utils';
import { getProjectEntity, getProjectStatusBody } from './utils';

describe('API project service', () => {
    const datasetIdentifier = getMockedDatasetIdentifier();
    const { datasetId, ...projectIdentifier } = datasetIdentifier;
    const { projectId, ...workspaceIdentifier } = projectIdentifier;
    const projectService = createApiProjectService();

    describe('Get projects', () => {
        it('gets list of projects without size information', async () => {
            const queryOptions: ProjectsQueryOptions = {
                sortDir: 'asc',
                sortBy: ProjectSortingOptions.name,
            };
            const mockProjects = [
                getMockedProjectDTO({
                    id: 'test-project1',
                    name: 'Test project 1',
                    creation_time: String(new Date('2021-07-08')),
                    thumbnail: 'v2/test-project1/thumbnail',
                    datasets: [
                        {
                            id: 'in-memory-dataset',
                            name: 'In memory dataset',
                            use_for_training: true,
                            creation_time: '2022-07-22T20:09:22.576000+00:00',
                        },
                    ],
                    storage_info: {},
                }),
                getMockedProjectDTO({
                    id: 'animal-project',
                    name: 'Animal project',
                    creation_time: String(new Date('2020-12-10')),
                    thumbnail: 'v2/animal-project/thumbnail',
                    datasets: [
                        {
                            id: 'in-memory-dataset',
                            name: 'In memory dataset',
                            use_for_training: true,
                            creation_time: '2022-07-22T20:09:22.576000+00:00',
                        },
                    ],
                    storage_info: {},
                }),
            ];
            const withSize = false;
            const projectUrl = API_URLS.PROJECTS(workspaceIdentifier);

            server.use(
                rest.get(projectUrl, (_req, res, ctx) => {
                    return res(ctx.json({ projects: mockProjects }));
                })
            );

            const { projects } = await projectService.getProjects(
                workspaceIdentifier,
                queryOptions,
                undefined,
                withSize
            );

            projects.forEach((project) => {
                expect(project).toEqual(expect.objectContaining({ storageInfo: {} }));
            });
        });

        it('gets list of projects with size information', async () => {
            const queryOptions: ProjectsQueryOptions = {
                sortDir: 'asc',
                sortBy: ProjectSortingOptions.name,
            };
            const mockProjects = [
                getMockedProjectDTO({
                    id: 'test-project1',
                    name: 'Test project 1',
                    creation_time: String(new Date('2021-07-08')),
                    thumbnail: 'v2/test-project1/thumbnail',
                    datasets: [
                        {
                            id: 'in-memory-dataset',
                            name: 'In memory dataset',
                            use_for_training: true,
                            creation_time: '2022-07-22T20:09:22.576000+00:00',
                        },
                    ],
                    storage_info: { size: 10000000 },
                }),
                getMockedProjectDTO({
                    id: 'animal-project',
                    name: 'Animal project',
                    creation_time: String(new Date('2020-12-10')),
                    thumbnail: 'v2/animal-project/thumbnail',
                    datasets: [
                        {
                            id: 'in-memory-dataset',
                            name: 'In memory dataset',
                            use_for_training: true,
                            creation_time: '2022-07-22T20:09:22.576000+00:00',
                        },
                    ],
                    storage_info: { size: 10000000 },
                }),
            ];
            const withSize = true;
            const projectUrl = API_URLS.PROJECTS(workspaceIdentifier);

            server.use(
                rest.get(projectUrl, (_req, res, ctx) => {
                    return res(ctx.json({ projects: mockProjects }));
                })
            );

            const { projects } = await projectService.getProjects(
                workspaceIdentifier,
                queryOptions,
                undefined,
                withSize
            );

            projects.forEach((project) => {
                expect(project).toEqual(expect.objectContaining({ storageInfo: { size: 10000000 } }));
            });
        });
    });

    describe('Get project', () => {
        it('gets project details', async () => {
            const projectUrl = API_URLS.PROJECT(datasetIdentifier);

            server.use(
                rest.get(projectUrl, (_req, res, ctx) => {
                    return res(ctx.json(PROJECT_RESPONSE()));
                })
            );

            const project: ProjectProps = await projectService.getProject(datasetIdentifier);

            const expectedProject: ProjectProps = getMockedProject({
                id: '60b609e0d036ba4566726c7f',
                name: 'Card detection',
                thumbnail: '/v2/projects/60b609e0d036ba4566726c7f/thumbnail',
                creationDate: new Date('2021-06-01T10:20:16.209Z'),
                domains: [DOMAIN.DETECTION],
                tasks: [
                    {
                        id: '60b609e0d036ba4566726c81',
                        labels: [
                            expect.objectContaining({
                                color: '#fff5f7ff',
                                group: 'Label Group 1',
                                id: '60b609e0d036ba4566726c82',
                                name: 'card',
                                hotkey: 'ctrl+1',
                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                            }),
                        ],
                        domain: DOMAIN.DETECTION,
                        title: 'Detection',
                    },
                ],
                labels: [
                    expect.objectContaining({
                        id: '60b609e0d036ba4566726c82',
                        name: 'card',
                        color: '#fff5f7ff',
                        group: 'Label Group 1',
                        hotkey: 'ctrl+1',
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                    }),
                ],
                datasets: [
                    {
                        id: 'training-dataset',
                        name: 'Training dataset',
                        useForTraining: true,
                        creationTime: '2022-07-22T20:09:22.576000+00:00',
                    },
                ],
            });

            expect(project).toStrictEqual(expectedProject);
        });
    });

    describe('Get project status', () => {
        const statusUrl = API_URLS.PROJECT_STATUS(projectIdentifier);

        it('gets project status - remaining time 189.18... return 3m:9s', async () => {
            server.use(
                rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) =>
                    res(ctx.json(getProjectStatusBody(189.18368864059448)))
                )
            );

            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.timeRemaining).toBe('3m:9s');
        });

        it('gets project status - remaining time 634 returns 10m:34s', async () => {
            server.use(
                rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) => res(ctx.json(getProjectStatusBody(634))))
            );

            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.timeRemaining).toBe('10m:34s');
        });

        it('gets project status - remaining time 12 returns 12s', async () => {
            server.use(rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) => res(ctx.json(getProjectStatusBody(12)))));

            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.timeRemaining).toBe('12s');
        });

        it('gets project status - remaining time 6661 returns 1h:51m:1s', async () => {
            server.use(
                rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) => res(ctx.json(getProjectStatusBody(6661))))
            );

            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.timeRemaining).toBe('1h:51m:1s');
        });

        it('gets project status - progress 90.123 returns 90%', async () => {
            server.use(
                rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) =>
                    res(ctx.json(getProjectStatusBody(undefined, 90.123)))
                )
            );

            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.progress).toBe('90%');
        });

        it('gets project status - progress 99.876 returns 99%', async () => {
            server.use(
                rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) =>
                    res(ctx.json(getProjectStatusBody(undefined, 99.876)))
                )
            );

            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.progress).toBe('99%');
        });

        it('gets project status - progress 100.0 returns 100%', async () => {
            server.use(
                rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) =>
                    res(ctx.json(getProjectStatusBody(undefined, 100.0)))
                )
            );

            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.progress).toBe('100%');
        });

        it('gets project status - progress 0.23 returns 0%', async () => {
            server.use(
                rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) =>
                    res(ctx.json(getProjectStatusBody(undefined, 0.23)))
                )
            );

            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.progress).toBe('0%');
        });

        it('gets project status - time -213 returns undefined', async () => {
            server.use(
                rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) => res(ctx.json(getProjectStatusBody(-213))))
            );
            const { trainingDetails } = await projectService.getProjectStatus(projectIdentifier);

            expect(trainingDetails?.timeRemaining).toBe(undefined);
        });
    });

    describe('Create project', () => {
        const url = API_URLS.PROJECTS(datasetIdentifier);

        const expectedDetectionTask = {
            title: 'Detection',
            task_type: 'detection',
            labels: [
                {
                    name: 'label',
                    group: 'group-1',
                    color: '#eeddbb',
                    parent_id: null,
                },
                {
                    name: 'label2',
                    group: 'group-1',
                    color: '#eeddbb',
                    parent_id: null,
                },
            ],
        };
        const expectedClassificationChainTask = {
            title: 'Classification',
            task_type: 'classification',
            labels: [
                {
                    name: 'label',
                    color: '#eeddbb',
                    group: `group-1${GROUP_SEPARATOR}Default group`,
                    parent_id: null,
                },
                {
                    name: 'label child',
                    color: '#eeddbb',
                    group: `group-1${GROUP_SEPARATOR}Default group`,
                    parent_id: 'label',
                    hotkey: 'ctrl+2',
                },
                {
                    name: 'label child child',
                    color: '#eeddbb',
                    group: `group-1${GROUP_SEPARATOR}Default group`,
                    parent_id: 'label child',
                    hotkey: 'ctrl+3',
                },
                {
                    name: 'label child2',
                    color: '#eeddbb',
                    group: `group-1${GROUP_SEPARATOR}Default group`,
                    parent_id: 'label',
                    hotkey: 'ctrl+4',
                },
            ],
        };

        const expectedClassificationTask = {
            title: 'Classification',
            task_type: 'classification',
            labels: [
                {
                    name: 'label',
                    color: '#eeddbb',
                    group: 'Default group',
                    parent_id: null,
                },
                {
                    name: 'label child',
                    color: '#eeddbb',
                    group: 'Default group',
                    parent_id: 'label',
                    hotkey: 'ctrl+2',
                },
                {
                    name: 'label child child',
                    color: '#eeddbb',
                    group: 'Default group',
                    parent_id: 'label child',
                    hotkey: 'ctrl+3',
                },
                {
                    name: 'label child2',
                    color: '#eeddbb',
                    group: 'Default group',
                    parent_id: 'label',
                    hotkey: 'ctrl+4',
                },
            ],
        };

        const expectedSegmentationTask = {
            title: 'Segmentation',
            task_type: 'segmentation',
            labels: [
                {
                    name: 'label',
                    color: '#eeddbb',
                    group: 'group-1',
                    parent_id: null,
                },
                {
                    name: 'label2',
                    color: '#eeddbb',
                    group: 'group-1',
                    parent_id: null,
                },
            ],
        };

        it('Create Detection', async () => {
            const expectedTasks = [{ title: 'Dataset', task_type: 'dataset' }, expectedDetectionTask];
            const expectedConnections = PROJECT_DETECTION.pipeline.connections;

            server.use(
                rest.post<ProjectCreation>(apiRequestUrl(url), (req, res, ctx) => {
                    const connections = req.body.pipeline.connections;
                    const tasks = req.body.pipeline.tasks;

                    if (!isEqual(expectedConnections, connections)) {
                        return res(ctx.status(500));
                    }

                    if (!isEqual(expectedTasks, tasks)) {
                        return res(ctx.status(500));
                    }

                    return res(ctx.json(PROJECT_DETECTION));
                })
            );

            const project = await projectService.createProject(
                workspaceIdentifier,
                'test-project',
                [DOMAIN.DETECTION],
                [
                    {
                        domain: DOMAIN.DETECTION,
                        labels: FLAT_LABELS,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                ]
            );

            expect(project).toStrictEqual(getProjectEntity(PROJECT_DETECTION));
        });

        it('Create Detection oriented', async () => {
            server.use(rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_DETECTION_ORIENTED))));

            const project = await projectService.createProject(
                workspaceIdentifier,
                'test-project',
                [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX],
                [
                    {
                        domain: DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
                        labels: FLAT_LABELS,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                ]
            );

            expect(project).toStrictEqual(getProjectEntity(PROJECT_DETECTION_ORIENTED));
        });

        it('Create Classification', async () => {
            const expectedConnections = [{ from: 'Dataset', to: 'Classification' }];
            const expectedTasks = [{ title: 'Dataset', task_type: 'dataset' }, expectedClassificationTask];

            server.use(
                rest.post<ProjectCreation>(apiRequestUrl(url), (req, res, ctx) => {
                    const connections = req.body.pipeline.connections;
                    const tasks = req.body.pipeline.tasks;

                    if (!isEqual(expectedConnections, connections)) {
                        return res(ctx.status(500));
                    }

                    if (!isEqual(expectedTasks, tasks)) {
                        return res(ctx.status(500));
                    }
                    return res(ctx.json(PROJECT_CLASSIFICATION));
                })
            );

            const project = await projectService.createProject(
                workspaceIdentifier,
                'test-project',
                [DOMAIN.CLASSIFICATION],
                [
                    {
                        domain: DOMAIN.CLASSIFICATION,
                        labels: HIERARCHY_LABELS,
                        relation: LabelsRelationType.MIXED,
                    },
                ]
            );

            expect(project).toStrictEqual(getProjectEntity(PROJECT_CLASSIFICATION));
        });

        it('Create Segmentation', async () => {
            server.use(rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_SEGMENTATION))));

            const project = await projectService.createProject(
                workspaceIdentifier,
                'test-project',
                [DOMAIN.SEGMENTATION],
                [
                    {
                        domain: DOMAIN.SEGMENTATION,
                        labels: FLAT_LABELS,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                ]
            );

            expect(project).toStrictEqual(getProjectEntity(PROJECT_SEGMENTATION));
        });

        it('Create Segmentation instance', async () => {
            server.use(rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_SEGMENTATION_INSTANCE))));

            const project = await projectService.createProject(
                workspaceIdentifier,
                'test-project',
                [DOMAIN.SEGMENTATION_INSTANCE],
                [
                    {
                        domain: DOMAIN.SEGMENTATION_INSTANCE,
                        labels: FLAT_LABELS,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                ]
            );

            expect(project).toStrictEqual(getProjectEntity(PROJECT_SEGMENTATION_INSTANCE));
        });

        it('Create Keypoint instance', async () => {
            server.use(rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_KEYPOINT_DETECTION))));

            const project = await projectService.createProject(
                workspaceIdentifier,
                'test-project',
                [DOMAIN.KEYPOINT_DETECTION],
                [
                    {
                        domain: DOMAIN.KEYPOINT_DETECTION,
                        labels: FLAT_LABELS,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                ]
            );

            expect(project).toStrictEqual(getProjectEntity(PROJECT_KEYPOINT_DETECTION));
        });

        describe('Create anomaly projects [FEATURE_FLAG_ANOMALY_REDUCTION:true]', () => {
            it('Create Anomaly classification', async () => {
                server.use(
                    rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_ANOMALY_CLASSIFICATION)))
                );
                const project = await projectService.createProject(
                    workspaceIdentifier,
                    'test-project',
                    [DOMAIN.ANOMALY_CLASSIFICATION],
                    [],
                    true
                );

                expect(project).toStrictEqual(getProjectEntity(PROJECT_ANOMALY_CLASSIFICATION));
            });

            it('Create Anomaly detection', async () => {
                server.use(
                    rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_ANOMALY_CLASSIFICATION)))
                );
                const project = await projectService.createProject(
                    workspaceIdentifier,
                    'test-project',
                    [DOMAIN.ANOMALY_DETECTION],
                    [],
                    true
                );

                expect(project).toStrictEqual(getProjectEntity(PROJECT_ANOMALY_CLASSIFICATION));
            });

            it('Create Anomaly segmentation', async () => {
                server.use(
                    rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_ANOMALY_CLASSIFICATION)))
                );
                const project = await projectService.createProject(
                    workspaceIdentifier,
                    'test-project',
                    [DOMAIN.ANOMALY_SEGMENTATION],
                    [],
                    true
                );

                expect(project).toStrictEqual(getProjectEntity(PROJECT_ANOMALY_CLASSIFICATION));
            });
        });

        describe('Create anomaly projects [FEATURE_FLAG_ANOMALY_REDUCTION:false]', () => {
            it('Create Anomaly classification', async () => {
                server.use(
                    rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_ANOMALY_CLASSIFICATION)))
                );
                const project = await projectService.createProject(
                    workspaceIdentifier,
                    'test-project',
                    [DOMAIN.ANOMALY_CLASSIFICATION],
                    []
                );

                expect(project).toStrictEqual(getProjectEntity(PROJECT_ANOMALY_CLASSIFICATION));
            });

            it('Create Anomaly detection', async () => {
                server.use(rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_ANOMALY_DETECTION))));
                const project = await projectService.createProject(
                    workspaceIdentifier,
                    'test-project',
                    [DOMAIN.ANOMALY_DETECTION],
                    []
                );

                expect(project).toStrictEqual(getProjectEntity(PROJECT_ANOMALY_DETECTION));
            });

            it('Create Anomaly segmentation', async () => {
                server.use(
                    rest.post(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_ANOMALY_SEGMENTATION)))
                );
                const project = await projectService.createProject(
                    workspaceIdentifier,
                    'test-project',
                    [DOMAIN.ANOMALY_SEGMENTATION],
                    []
                );

                expect(project).toStrictEqual(getProjectEntity(PROJECT_ANOMALY_SEGMENTATION));
            });
        });

        it('Create Detection > Classification', async () => {
            const expectedConnections = [
                { from: 'Dataset', to: 'Detection' },
                { from: 'Detection', to: 'Crop' },
                { from: 'Crop', to: 'Classification' },
            ];
            const expectedTasks = [
                { title: 'Dataset', task_type: 'dataset' },
                expectedDetectionTask,
                expectedClassificationChainTask,
                {
                    title: 'Crop',
                    task_type: 'crop',
                },
            ];

            server.use(
                rest.post<ProjectCreation>(apiRequestUrl(url), (req, res, ctx) => {
                    const connections = req.body.pipeline.connections;
                    const tasks = req.body.pipeline.tasks;

                    if (!isEqual(expectedConnections, connections)) {
                        return res(ctx.status(500));
                    }

                    if (!isEqual(expectedTasks, tasks)) {
                        return res(ctx.status(500));
                    }

                    return res(ctx.json(PROJECT_DETECTION_CLASSIFICATION));
                })
            );

            const project = await projectService.createProject(
                workspaceIdentifier,
                'test-project',
                [DOMAIN.DETECTION, DOMAIN.CROP, DOMAIN.CLASSIFICATION],
                [
                    { domain: DOMAIN.DETECTION, labels: FLAT_LABELS, relation: LabelsRelationType.SINGLE_SELECTION },
                    { domain: DOMAIN.CLASSIFICATION, labels: HIERARCHY_LABELS, relation: LabelsRelationType.MIXED },
                ]
            );

            expect(project).toStrictEqual(getProjectEntity(PROJECT_DETECTION_CLASSIFICATION));
        });

        it('Create Detection > Segmentation', async () => {
            const expectedConnections = [
                { from: 'Dataset', to: 'Detection' },
                { from: 'Detection', to: 'Crop' },
                { from: 'Crop', to: 'Segmentation' },
            ];
            const expectedTasks = [
                { title: 'Dataset', task_type: 'dataset' },
                expectedDetectionTask,
                {
                    ...expectedSegmentationTask,
                    labels: expectedSegmentationTask.labels.map((task) => ({
                        ...task,
                        group: `group-1${GROUP_SEPARATOR}${task.group}`,
                    })),
                },
                {
                    title: 'Crop',
                    task_type: 'crop',
                },
            ];

            server.use(
                rest.post<ProjectCreation>(apiRequestUrl(url), (req, res, ctx) => {
                    const connections = req.body.pipeline.connections;
                    const tasks = req.body.pipeline.tasks;

                    if (!isEqual(expectedConnections, connections)) {
                        return res(ctx.status(500));
                    }

                    if (!isEqual(expectedTasks, tasks)) {
                        return res(ctx.status(500));
                    }

                    return res(ctx.json(PROJECT_DETECTION_SEGMENTATION));
                })
            );

            const project = await projectService.createProject(
                workspaceIdentifier,
                'test-project',
                [DOMAIN.DETECTION, DOMAIN.CROP, DOMAIN.SEGMENTATION],
                [
                    { domain: DOMAIN.DETECTION, labels: FLAT_LABELS, relation: LabelsRelationType.SINGLE_SELECTION },
                    { domain: DOMAIN.SEGMENTATION, labels: FLAT_LABELS, relation: LabelsRelationType.SINGLE_SELECTION },
                ]
            );

            expect(project).toStrictEqual(getProjectEntity(PROJECT_DETECTION_SEGMENTATION));
        });
    });

    describe('Edit project', () => {
        const url = API_URLS.PROJECT(datasetIdentifier);

        it('edits project correctly', async () => {
            const fakeProject: EditProjectProps = getMockedProject({
                id: 'fake-project-id',
                name: 'fake project',
                creationDate: new Date(),
                domains: [DOMAIN.ANOMALY_DETECTION],
                thumbnail: '',
                tasks: [getMockedTask({ domain: DOMAIN.ANOMALY_DETECTION, id: '123' })],
                datasets: [
                    {
                        name: 'test dataset',
                        id: 'test-dataset',
                        useForTraining: false,
                        creationTime: '2022-07-22T20:09:22.576000+00:00',
                    },
                ],
            });

            server.use(
                rest.get(apiRequestUrl(url), (_req, res, ctx) => res(ctx.json(PROJECT_DETECTION))),
                rest.put<{ result: string }>(apiRequestUrl(url), (_req, res, ctx) => {
                    return res(ctx.json({ ...PROJECT_DETECTION, name: 'updated-name' }));
                })
            );

            const project = await projectService.editProject(datasetIdentifier, fakeProject);

            expect(project).toStrictEqual(getProjectEntity({ ...PROJECT_DETECTION, name: 'updated-name' }));
        });
    });

    describe('Project dataset', () => {
        it('creates dataset', async () => {
            const url = API_URLS.DATASET.CREATE_DATASET(datasetIdentifier);
            server.use(
                rest.post<CreateDatasetResponseDTO>(apiRequestUrl(url), (_req, res, ctx) => {
                    return res(
                        ctx.json({
                            id: 'some-id',
                            name: 'testing dataset',
                            use_for_training: false,
                            creation_time: '1234',
                        })
                    );
                })
            );

            const result = await projectService.createDataset({
                projectIdentifier: datasetIdentifier,
                name: 'dataset',
            });

            expect(result).toEqual({
                id: 'some-id',
                name: 'testing dataset',
                useForTraining: false,
                creationTime: '1234',
            });
        });

        it('deletes dataset', async () => {
            const url = API_URLS.DATASET.DELETE_DATASET(datasetIdentifier);

            server.use(
                rest.delete<DeleteDatasetResponse>(apiRequestUrl(url), (_req, res, ctx) => {
                    return res(ctx.json({ result: 'ok' }));
                })
            );

            const result = await projectService.deleteDataset(datasetIdentifier);

            expect(result).toEqual('ok');
        });

        it('updates dataset', async () => {
            const url = API_URLS.DATASET.UPDATE_DATASET(datasetIdentifier);
            const mockDataset = {
                id: 'some-id',
                name: 'updated name',
                useForTraining: false,
                creationTime: '1234',
            };

            server.use(
                rest.put<CreateDatasetResponseDTO>(apiRequestUrl(url), (_req, res, ctx) => {
                    return res(
                        ctx.json({
                            id: mockDataset.id,
                            name: mockDataset.name,
                            use_for_training: mockDataset.useForTraining,
                            creation_time: mockDataset.creationTime,
                        })
                    );
                })
            );

            const result = await projectService.updateDataset(datasetIdentifier, mockDataset);

            expect(result).toEqual({
                id: 'some-id',
                name: 'updated name',
                useForTraining: false,
                creationTime: '1234',
            });
        });
    });

    describe('Dataset import/export', () => {
        const mockDatasetIdentifier = {
            workspaceId: 'workspace_1',
            projectId: 'project-id',
            datasetId: 'dataset_1',
            organizationId: 'organization-id',
        };

        describe('Export', () => {
            const datasetJobId = 'some-dataset-id';
            const datasetPrepareExportURL = API_URLS.DATASET.PREPARE_EXPORT(
                mockDatasetIdentifier,
                ExportFormats.YOLO,
                true
            );
            const datasetExportURL = API_URLS.DATASET.EXPORT_STATUS(mockDatasetIdentifier, datasetJobId);

            it('prepares export dataset job', async () => {
                server.use(
                    rest.post(apiRequestUrl(datasetPrepareExportURL), (_req, res, ctx) =>
                        res(ctx.json({ job_id: datasetJobId }))
                    )
                );

                const response = await projectService.prepareExportDatasetJob({
                    ...mockDatasetIdentifier,
                    exportFormat: ExportFormats.YOLO,
                    saveVideoAsImages: true,
                });

                expect(response).toEqual({ jobId: datasetJobId });
            });

            it('export dataset status', async () => {
                server.use(
                    rest.get(apiRequestUrl(datasetExportURL), (_req, res, ctx) =>
                        res(
                            ctx.json({
                                state: ExportStatusStateDTO.DONE,
                                message: 'success',
                                progress: 100,
                                download_url: 'some-url',
                            })
                        )
                    )
                );

                const response = await projectService.exportDatasetStatus({
                    ...mockDatasetIdentifier,
                    exportDatasetId: 'some-dataset-id',
                });

                expect(response).toEqual({
                    state: ExportStatusStateDTO.DONE,
                    message: 'success',
                    progress: 100,
                    download_url: 'some-url',
                });
            });
        });
    });
});
