// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Task } from '@/api/types';
import dayjs from 'dayjs';

import { i18n } from '../../../i18n';
import { isMultiLabelClassificationTask } from '../task-type-guards';

export const formatCreationDate = (creationDate: string) => {
    return dayjs(creationDate).format('D MMMM YYYY | h:mm A');
};

export const getProjectTypeTitle = (task?: Task): string | undefined => {
    if (task === undefined) {
        return undefined;
    }

    return isMultiLabelClassificationTask(task)
        ? i18n.t('taskTypes.multiLabelClassification')
        : i18n.t(`taskTypes.${task.task_type}`);
};
