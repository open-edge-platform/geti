// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Project } from '../../../../constants/shared-types';
import { isMultiLabelClassificationTask } from '../../task-type-guards';

export type TaskCategory =
    | 'classification'
    | 'multi_label_classification'
    | 'detection'
    | 'instance_segmentation';

export const TASK_CATEGORY_LABELS: Record<TaskCategory, string> = {
    classification: 'Classification',
    multi_label_classification: 'Multi-label classification',
    detection: 'Object detection',
    instance_segmentation: 'Instance segmentation',
};

// Each task category has its own colour so filtered projects are easily distinguishable.
// Colours are chosen to keep enough contrast with white text.
export const TASK_CATEGORY_COLORS: Record<TaskCategory, string> = {
    classification: '#7454c9',
    multi_label_classification: '#c93f9e',
    detection: '#0e8a7d',
    instance_segmentation: '#b5651d',
};

export const TASK_CATEGORY_OPTIONS: TaskCategory[] = [
    'classification',
    'multi_label_classification',
    'detection',
    'instance_segmentation',
];

export const getProjectTaskCategory = (project: Project): TaskCategory => {
    if (isMultiLabelClassificationTask(project.task)) {
        return 'multi_label_classification';
    }

    return project.task.task_type as TaskCategory;
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
