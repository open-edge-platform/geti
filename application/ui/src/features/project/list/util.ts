// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Task, TaskType } from '@/api/types';
import { i18n, type TranslateFn } from '@/i18n';

import { isMultiLabelClassificationTask } from '../task-type-guards';

export const formatCreationDate = (creationDate: string, locale = i18n.resolvedLanguage ?? i18n.language): string => {
    return new Intl.DateTimeFormat(locale, {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
    }).format(new Date(creationDate));
};

export const MAP_PROJECT_TYPE_TO_TITLE_KEY = {
    detection: 'project.taskTypes.detection',
    classification: 'project.taskTypes.classification',
    instance_segmentation: 'project.taskTypes.instanceSegmentation',
} as const satisfies Record<TaskType, string>;

export const getProjectTypeTitle = (task: Task | undefined, t: TranslateFn): string | undefined => {
    if (task === undefined) {
        return undefined;
    }

    return isMultiLabelClassificationTask(task)
        ? t('project.taskTypes.multiLabelClassification')
        : t(MAP_PROJECT_TYPE_TO_TITLE_KEY[task.task_type]);
};
