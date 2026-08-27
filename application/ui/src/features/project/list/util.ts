// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Task } from '@/api/types';

import { i18n } from '../../../i18n';
import { isMultiLabelClassificationTask } from '../task-type-guards';

export const formatCreationDate = (creationDate: string): string => {
    const date = new Date(creationDate);
    const language = i18n.language;

    const day = new Intl.DateTimeFormat(language, { day: 'numeric', month: 'long', year: 'numeric' }).format(date);
    const time = new Intl.DateTimeFormat(language, { hour: 'numeric', minute: '2-digit', hour12: true }).format(date);

    return `${day} | ${time}`;
};

export const getProjectTypeTitle = (task?: Task): string | undefined => {
    if (task === undefined) {
        return undefined;
    }

    return isMultiLabelClassificationTask(task)
        ? i18n.t('taskTypes.multiLabelClassification')
        : i18n.t(`taskTypes.${task.task_type}`);
};
