// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { isEmpty } from 'lodash-es';

import { Project, TaskType } from '../../../../constants/shared-types';

// Each task type has its own colour so filtered projects are easily distinguishable.
// Colours are chosen to keep enough contrast against the app's light background.
export const TASK_TYPE_COLORS: Record<TaskType, string> = {
    classification: '#7454c9',
    detection: '#0e8a7d',
    instance_segmentation: '#b5651d',
};

export const TASK_TYPE_OPTIONS: TaskType[] = ['classification', 'detection', 'instance_segmentation'];

export const filterProjects = (projects: Project[], searchName: string, selectedTaskTypes: TaskType[]): Project[] => {
    const normalizedSearch = searchName.trim().toLocaleLowerCase();

    return projects.filter((project) => {
        const matchesName = isEmpty(normalizedSearch) || project.name.toLocaleLowerCase().includes(normalizedSearch);
        const matchesTaskType = isEmpty(selectedTaskTypes) || selectedTaskTypes.includes(project.task.task_type);

        return matchesName && matchesTaskType;
    });
};
