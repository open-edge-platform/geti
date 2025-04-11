// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { EditedLabelDTO } from '../../core/labels/dtos/label.interface';
import { DOMAIN } from '../../core/projects/core.interface';
import { isAnomalyDomain } from '../../core/projects/domains';
import { ProjectDTO } from '../../core/projects/dtos/project.interface';
import { ProjectStatusDTO, ProjectStatusTaskDTO } from '../../core/projects/dtos/status.interface';
import { TASK_TYPE } from '../../core/projects/dtos/task.interface';
import { ProjectStatus } from '../../core/projects/project-status.interface';
import { ProjectProps } from '../../core/projects/project.interface';
import { Performance, PerformanceType, Task } from '../../core/projects/task.interface';
import { ProjectContextProps } from '../../pages/project-details/providers/project-provider/project-provider.interface';
import { getMockedProjectIdentifier } from './mocked-identifiers';

const mockedTask: Task = {
    id: 'task',
    title: 'Task',
    domain: DOMAIN.CLASSIFICATION,
    labels: [],
};

const getMockedTask = (customTaskValues: Partial<Task>): Task => {
    return {
        ...mockedTask,
        ...customTaskValues,
    };
};

const mockedProject: ProjectProps = {
    id: '111111',
    name: 'Test project 1',
    thumbnail: 'test/thumbnail',
    labels: [],
    creationDate: new Date(),
    domains: [DOMAIN.DETECTION, DOMAIN.CLASSIFICATION],
    tasks: [
        getMockedTask({ id: 'detection', domain: DOMAIN.DETECTION }),
        getMockedTask({ id: 'classification', domain: DOMAIN.CLASSIFICATION }),
    ],
    performance: {
        type: PerformanceType.DEFAULT,
        score: 0.768,
        taskPerformances: [
            {
                score: {
                    value: 0.768,
                    metricType: 'accuracy',
                },
                taskNodeId: 'task-id',
            },
        ],
    },
    datasets: [
        {
            id: 'mocked-dataset',
            name: 'Mocked dataset',
            useForTraining: true,
            creationTime: '2022-07-22T20:09:22.576000+00:00',
        },
    ],
    storageInfo: {},
};

export const getMockedPerformance = (customProjectValues: Partial<ProjectProps>, score: number | null): Performance => {
    if (customProjectValues.performance) {
        return customProjectValues.performance;
    }

    const tasks = customProjectValues.tasks ?? [];

    if (tasks.some(({ domain }) => isAnomalyDomain(domain))) {
        return {
            type: PerformanceType.ANOMALY,
            score,
            globalScore: score,
            localScore: score,
            taskPerformances: tasks.map(({ domain, id }) => {
                if (score === null) {
                    return {
                        domain,
                        score: null,
                        globalScore: null,
                        localScore: null,
                        taskNodeId: id,
                    };
                }

                return {
                    domain,
                    score: {
                        value: score,
                        metricType: 'accuracy',
                    },
                    globalScore: {
                        value: score,
                        metricType: 'accuracy',
                    },
                    localScore: {
                        value: score,
                        metricType: 'accuracy',
                    },
                    taskNodeId: id,
                };
            }),
        };
    }

    return {
        type: PerformanceType.DEFAULT,
        score,
        taskPerformances: tasks.map(({ domain, id }) => ({
            domain,
            score: score === null ? null : { value: score, metricType: 'accuracy' },
            taskNodeId: id,
        })),
    };
};

export const getMockedProject = (customProjectValues: Partial<ProjectProps>): ProjectProps => {
    // As domains should be inferred from a project's task we give priority to the tasks' domains,
    // this should, in the future, allow us to remove the domains property from ProjectProps
    const domains =
        customProjectValues.tasks?.map(({ domain }) => domain) ?? customProjectValues.domains ?? mockedProject.domains;

    const labels =
        customProjectValues.tasks?.flatMap((task) => task.labels) ?? customProjectValues.labels ?? mockedProject.labels;
    const performance = getMockedPerformance(customProjectValues, 0.768);

    return {
        ...mockedProject,
        ...customProjectValues,
        performance,
        domains,
        labels,
    };
};

export const getMockedProjectDTO = (
    customProjectDTOValues: Partial<ProjectDTO>,
    labels?: EditedLabelDTO[]
): ProjectDTO => {
    const projectDTO: ProjectDTO = {
        name: 'Test project',
        id: 'test-project',
        thumbnail: '/thumbnail',
        creation_time: '2022-07-22T20:09:22.576000+00:00',
        performance: {
            score: 0.9,
            task_performances: [{ task_id: 'task-id', score: { value: 0.9, metric_type: 'accuracy' } }],
        },
        datasets: [
            {
                id: 'dataset-id',
                name: 'Dataset',
                creation_time: '2022-07-22T20:09:22.576000+00:00',
                use_for_training: false,
            },
        ],
        pipeline: {
            connections: [
                {
                    from: 'dataset-id',
                    to: 'task-id',
                },
            ],
            tasks: [
                {
                    id: 'task-id',
                    labels: labels || ([] as EditedLabelDTO[]),
                    title: 'Task',
                    task_type: TASK_TYPE.CLASSIFICATION,
                },
            ],
        },
        storage_info: {},
    };

    return { ...projectDTO, ...customProjectDTOValues };
};

export const mockedProjectContextProps = (customValues: Partial<ProjectContextProps>): ProjectContextProps => ({
    isTaskChainProject: false,
    projectIdentifier: getMockedProjectIdentifier({ workspaceId: '321', projectId: '123' }),
    project: getMockedProject({ domains: [] }),
    isSingleDomainProject: () => true,
    isTaskChainDomainProject: () => true,
    score: 20,
    error: null,
    reload: () => true,
    ...customValues,
});

export const getMockedProjectStatusTask = (
    customTaskValues: Partial<ProjectStatusTaskDTO> = {}
): ProjectStatusTaskDTO => {
    return {
        id: 'id',
        status: {
            progress: 0,
            time_remaining: 0,
        },
        required_annotations: {
            value: 12,
            details: [
                {
                    id: '1',
                    value: 12,
                    label_color: 'red',
                    label_name: 'cow',
                },
            ],
        },
        ready_to_train: true,
        is_training: false,
        n_new_annotations: 0,
        title: 'hello',
        ...customTaskValues,
    };
};

export const getMockedProjectStatus = (customProjectStatusValues: Partial<ProjectStatus> = {}): ProjectStatus => {
    return {
        isTraining: false,
        performance: {
            type: PerformanceType.DEFAULT,
            score: null,
            taskPerformances: [],
        },
        trainingDetails: undefined,
        tasks: [getMockedProjectStatusTask()],
        ...customProjectStatusValues,
    };
};

export const getMockedProjectStatusDTO = (
    customProjectStatusValues: Partial<ProjectStatusDTO> = {}
): ProjectStatusDTO => {
    return {
        is_training: false,
        n_required_annotations: 0,
        project_performance: {
            score: null,
            task_performances: [],
        },
        tasks: [getMockedProjectStatusTask()],
        status: {
            progress: 0,
            time_remaining: 0,
        },
        ...customProjectStatusValues,
    };
};
