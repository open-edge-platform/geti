// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Project, TaskType } from '@/api/types';
import { isEmpty } from 'lodash-es';

export const TASK_TYPE_OPTIONS: TaskType[] = ['classification', 'detection', 'instance_segmentation'];

export const filterProjects = (projects: Project[], searchName: string, selectedTaskTypes: TaskType[]): Project[] => {
    const normalizedSearch = searchName.trim().toLocaleLowerCase();

    return projects.filter((project) => {
        const matchesName = isEmpty(normalizedSearch) || project.name.toLocaleLowerCase().includes(normalizedSearch);
        const matchesTaskType = isEmpty(selectedTaskTypes) || selectedTaskTypes.includes(project.task.task_type);

        return matchesName && matchesTaskType;
    });
};
