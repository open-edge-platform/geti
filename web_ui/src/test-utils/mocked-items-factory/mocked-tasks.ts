// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../core/projects/core.interface';
import { KeypointTask, Task } from '../../core/projects/task.interface';
import { TaskContextProps } from '../../pages/annotator/providers/task-provider/task-provider.component';

const mockedTask: Task = {
    id: 'task',
    title: 'Task',
    domain: DOMAIN.CLASSIFICATION,
    labels: [],
};

export const getMockedTask = (customTaskValues: Partial<Task> = {}): Task => {
    return {
        ...mockedTask,
        ...customTaskValues,
    };
};

export const getMockedKeypointTask = (customTaskValues: Partial<KeypointTask>): KeypointTask => {
    return {
        ...mockedTask,
        keypointStructure: { edges: [], positions: [] },
        ...customTaskValues,
        domain: DOMAIN.KEYPOINT_DETECTION,
    };
};

export const mockedTaskContextProps = (customValues: Partial<TaskContextProps>): TaskContextProps => ({
    tasks: [],
    selectedTask: null,
    previousTask: null,
    setSelectedTask: jest.fn(),
    defaultLabel: null,
    setDefaultLabel: jest.fn(),
    isTaskChainDomainSelected: (_domain: DOMAIN) => false,
    activeDomains: [],
    labels: [],
    isTaskChainSecondTask: false,
    ...customValues,
});
