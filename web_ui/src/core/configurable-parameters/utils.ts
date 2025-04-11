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

import isEqual from 'lodash/isEqual';

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
