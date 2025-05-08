// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEqual } from 'lodash-es';

import {
    BooleanGroupParams,
    ConfigurableParametersTaskChain,
    NumberGroupParams,
} from '../../shared/components/configurable-parameters/configurable-parameters.interface';

const hasEqualHeader =
    <T extends { header: string }>(toFind: string | null | undefined) =>
    ({ header }: T) =>
        isEqual(toFind, header);

const getConfigByTaskId = (taskId: string) => (task: ConfigurableParametersTaskChain) => taskId === task.taskId;

export const findAutoTrainingConfig = (
    taskId: string,
    config: ConfigurableParametersTaskChain[]
): BooleanGroupParams | undefined => {
    const taskConfig = config?.find(getConfigByTaskId(taskId));
    const generalConfig = taskConfig?.components?.find(hasEqualHeader('General'));

    const parameterGroup = generalConfig?.parameters?.find(hasEqualHeader('Auto-training'));

    if (parameterGroup === undefined || parameterGroup.dataType !== 'boolean') {
        return undefined;
    }

    return parameterGroup;
};

export const findDynamicRequiredAnnotationsConfig = (
    taskId: string,
    config: ConfigurableParametersTaskChain[]
): BooleanGroupParams | undefined => {
    const taskConfig = config?.find(getConfigByTaskId(taskId));
    const generalConfig = taskConfig?.components?.find(hasEqualHeader('Annotation requirements'));

    const parameterGroup = generalConfig?.parameters?.find(hasEqualHeader('Dynamic required annotations'));

    if (parameterGroup === undefined || parameterGroup.dataType !== 'boolean') {
        return undefined;
    }

    return parameterGroup;
};

export const findRequiredImagesAutoTrainingConfig = (
    taskId: string,
    config: ConfigurableParametersTaskChain[]
): NumberGroupParams | undefined => {
    const taskConfig = config?.find(getConfigByTaskId(taskId));
    const generalConfig = taskConfig?.components?.find(hasEqualHeader('Annotation requirements'));

    const parameterGroup = generalConfig?.parameters?.find(({ name }) => name === 'required_images_auto_training');

    // Only the NumberGroupParams contain minValue and maxValue
    if (parameterGroup !== undefined && 'minValue' in parameterGroup && 'maxValue' in parameterGroup) {
        return parameterGroup;
    }

    return undefined;
};
