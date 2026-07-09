// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotationType, TaskType } from '@/api/types';

export const TASK_SELECTION_FORM_ID = 'task-selection-form';

export const getAllowedTaskTypes = (annotationType: AnnotationType | undefined): TaskType[] => {
    if (annotationType === 'label') {
        return ['classification'];
    }

    return ['classification', 'detection', 'instance_segmentation'];
};

export const getRecommendedTaskType = (annotationType: AnnotationType | undefined): TaskType | undefined => {
    switch (annotationType) {
        case 'bounding_box':
            return 'detection';
        case 'polygon':
            return 'instance_segmentation';
        case 'label':
            return 'classification';
        default:
            return undefined;
    }
};
