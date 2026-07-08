// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Project, TaskType } from '../../../../constants/shared-types';

export type TaskCategory = TaskType;

export const TASK_CATEGORY_LABELS: Record<TaskCategory, string> = {
    classification: 'Classification',
    detection: 'Detection',
    instance_segmentation: 'Segmentation',
};

// Each task category has its own colour so filtered projects are easily distinguishable.
// Colours are chosen to keep enough contrast with white text.
export const TASK_CATEGORY_COLORS: Record<TaskCategory, string> = {
    classification: '#7454c9',
    detection: '#0e8a7d',
    instance_segmentation: '#b5651d',
};

export const TASK_CATEGORY_OPTIONS: TaskCategory[] = ['classification', 'detection', 'instance_segmentation'];

export const getProjectTaskCategory = (project: Project): TaskCategory => {
    return project.task.task_type;
};

export const filterProjects = (
    projects: Project[],
    searchName: string,
    selectedCategories: TaskCategory[]
): Project[] => {
    const normalizedSearch = searchName.trim().toLocaleLowerCase();

    return projects.filter((project) => {
        const matchesName =
            normalizedSearch === '' || project.name.toLocaleLowerCase().includes(normalizedSearch);

        const matchesTaskType =
            selectedCategories.length === 0 || selectedCategories.includes(getProjectTaskCategory(project));

        return matchesName && matchesTaskType;
    });
};
