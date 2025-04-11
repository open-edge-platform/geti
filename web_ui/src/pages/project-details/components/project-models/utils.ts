// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ConfigurableParametersComponentsBodyDTO } from '../../../../core/configurable-parameters/dtos/configurable-parameters.interface';
import { ModelGroupsAlgorithmDetails, ModelsGroups } from '../../../../core/models/models.interface';
import { PerformanceCategory } from '../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { TaskWithSupportedAlgorithms } from '../../../../core/supported-algorithms/supported-algorithms.interface';
import {
    ConfigurableParametersComponents,
    ConfigurableParametersTaskChain,
} from '../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { getComponentsDTO } from '../../../../shared/components/configurable-parameters/utils';
import { hasEqualId } from '../../../../shared/utils';

export const getSelectedComponent = (
    configParameters: ConfigurableParametersTaskChain[] | undefined,
    selectedComponentId: string | undefined
): ConfigurableParametersComponents | undefined => {
    return configParameters?.map((config) => config.components.find(hasEqualId(selectedComponentId))).find(Boolean);
};

export const getTrainingConfigParametersDTO = ({
    components,
}: ConfigurableParametersTaskChain): { components: ConfigurableParametersComponentsBodyDTO[] } => {
    return {
        components: getComponentsDTO(components),
    };
};

export const addAlgorithmDetails =
    (tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms) =>
    (model: ModelsGroups): ModelGroupsAlgorithmDetails => {
        const match = tasksWithSupportedAlgorithms[model.taskId]?.find(({ name }) => name === model.groupName);

        return {
            ...model,
            isDefaultAlgorithm: match?.isDefaultAlgorithm ?? false,
            performanceCategory: match?.performanceCategory ?? PerformanceCategory.OTHER,
            complexity: match?.gigaflops ?? null,
        };
    };
