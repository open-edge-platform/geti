// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties } from 'react';

import isEqual from 'lodash/isEqual';

import { Task } from '../../../../core/projects/task.interface';
import { BooleanGroupParams, NumberGroupParams } from '../../configurable-parameters/configurable-parameters.interface';

interface AutoTrainingNotificationConfig {
    text: 'ON' | 'OFF' | 'SPLIT';
    isVisible: boolean;
    styles: CSSProperties;
}

export interface AutoTrainingTask {
    task: Task;
    trainingConfig?: BooleanGroupParams;
    dynamicRequiredAnnotationsConfig?: BooleanGroupParams;
    requiredImagesAutoTrainingConfig?: NumberGroupParams;
}

export const getAllAutoTrainingValue = (autoTrainingTasks: AutoTrainingTask[]) => {
    const [firstTask, ...otherTasks] = autoTrainingTasks;
    const firstValue = firstTask?.trainingConfig?.value;
    const allEqualsValues = otherTasks.every(({ trainingConfig }) => isEqual(firstValue, trainingConfig?.value));

    return allEqualsValues ? Boolean(firstValue) : null;
};

export const getNotificationConfig = (value: boolean | null): AutoTrainingNotificationConfig => {
    switch (value) {
        case true:
            return {
                text: 'ON',
                isVisible: true,
                styles: {
                    color: 'var(--spectrum-global-color-gray-50)',
                    backgroundColor: 'var(--brand-moss)',
                },
            };
        case false:
            return {
                text: 'OFF',
                isVisible: true,
                styles: {
                    color: 'var(--spectrum-global-color-gray-900)',
                    backgroundColor: 'var(--brand-coral-coral-shade1)',
                },
            };
        default:
            return {
                text: 'SPLIT',
                isVisible: false,
                styles: {
                    background:
                        'linear-gradient(to right bottom, var(--brand-coral-coral-shade1) 50%, var(--brand-moss) 50%)',
                },
            };
    }
};
