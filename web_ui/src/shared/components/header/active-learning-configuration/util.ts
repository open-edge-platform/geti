// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { isEqual } from 'lodash-es';

import {
    BooleanGroupParams,
    NumberGroupParams,
} from '../../../../core/configurable-parameters/services/configurable-parameters.interface';
import {
    BoolParameter,
    ConfigurationParameter,
    NumberParameter,
} from '../../../../core/configurable-parameters/services/configuration.interface';
import { Task } from '../../../../core/projects/task.interface';

interface AutoTrainingNotificationConfig {
    text: 'ON' | 'OFF' | 'SPLIT';
    isVisible: boolean;
    styles: CSSProperties;
}

interface AutoTrainingTask {
    task: Task;
    trainingConfig?: BooleanGroupParams | BoolParameter;
    dynamicRequiredAnnotationsConfig?: BooleanGroupParams | BoolParameter;
    requiredImagesAutoTrainingConfig?: NumberGroupParams | NumberParameter;
}

export interface UseActiveLearningConfigurationReturnType {
    autoTrainingTasks: AutoTrainingTask[];
    isPending: boolean;
    updateAutoTraining: (taskId: string, value: boolean) => void;
    updateDynamicRequiredAnnotations: (taskId: string, value: boolean) => void;
    updateRequiredImagesAutoTraining: (taskId: string, value: number) => void;
}

export const getAllAutoTrainingValue = (autoTrainingValues: boolean[]) => {
    const [firstTaskAutoTrainingValue, ...otherTasks] = autoTrainingValues;
    const allEqualsValues = otherTasks.every((otherAutoTrainingValue) =>
        isEqual(firstTaskAutoTrainingValue, otherAutoTrainingValue)
    );

    return allEqualsValues ? firstTaskAutoTrainingValue : null;
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

export const getAutoTrainingEnabledParameter = (parameters: ConfigurationParameter[]): BoolParameter | undefined => {
    const autoTrainingParameter = parameters.find((config) => config.key === 'enable');

    if (autoTrainingParameter !== undefined && autoTrainingParameter.type === 'bool') {
        return autoTrainingParameter;
    }

    return undefined;
};

export const getDynamicRequiredAnnotationsParameter = (
    parameters: ConfigurationParameter[]
): BoolParameter | undefined => {
    const dynamicRequiredAnnotationsParameter = parameters.find(
        (config) => config.key === 'enable_dynamic_required_annotations'
    );

    if (dynamicRequiredAnnotationsParameter !== undefined && dynamicRequiredAnnotationsParameter.type === 'bool') {
        return dynamicRequiredAnnotationsParameter;
    }

    return undefined;
};

export const getRequiredImagesAutoTrainingParameter = (
    parameters: ConfigurationParameter[]
): NumberParameter | undefined => {
    const requiredImagesAutoTrainingParameter = parameters.find((config) => config.key === 'min_images_per_label');

    if (requiredImagesAutoTrainingParameter !== undefined && requiredImagesAutoTrainingParameter.type === 'int') {
        return requiredImagesAutoTrainingParameter;
    }

    return undefined;
};
