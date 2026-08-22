// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Task, TaskType } from '@/api/types';
import dayjs from 'dayjs';

import { i18n } from '../../../i18n';
import { isMultiLabelClassificationTask } from '../task-type-guards';

export const formatCreationDate = (creationDate: string) => {
    return dayjs(creationDate).format('D MMMM YYYY | h:mm A');
};

const TASK_TYPE_TO_TITLE_KEY: Record<TaskType, string> = {
    detection: 'taskTypes.detection',
    classification: 'taskTypes.classification',
    instance_segmentation: 'taskTypes.instanceSegmentation',
};

export const getTaskTypeTitle = (taskType: TaskType): string => {
    return i18n.t(TASK_TYPE_TO_TITLE_KEY[taskType]);
};

export const getProjectTypeTitle = (task?: Task): string | undefined => {
    if (task === undefined) {
        return undefined;
    }

    return isMultiLabelClassificationTask(task)
        ? i18n.t('taskTypes.multiLabelClassification')
        : getTaskTypeTitle(task.task_type);
};
