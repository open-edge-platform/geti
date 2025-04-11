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

import {
    ConfigurableParametersComponentsBodyDTO,
    ConfigurableParametersParamsReconfigureDTO,
    ConfigurableParametersReconfigureDTO,
    EntityIdentifierDTO,
} from '../../../core/configurable-parameters/dtos/configurable-parameters.interface';
import { isNonEmptyArray } from '../../utils';
import {
    ConfigurableParametersComponents,
    ConfigurableParametersGroups,
    ConfigurableParametersParams,
    ConfigurableParametersTaskChain,
    EntityIdentifier,
} from './configurable-parameters.interface';

export const isLearningParametersTab = (entityIdentifier: EntityIdentifier): boolean => {
    return entityIdentifier.type === 'HYPER_PARAMETER_GROUP' && entityIdentifier.groupName === 'learning_parameters';
};

const NUMBER_OF_CONCATENATED_IDS_WITH_GROUPS = 4; // taskId::componentId::groupId::parameterId

export const getNewParameterValue = <T extends string | boolean | number>(
    parameter: ConfigurableParametersParams,
    value: T
): ConfigurableParametersParams => {
    if (parameter.dataType === 'string' && typeof value === 'string') {
        return {
            ...parameter,
            value,
        };
    } else if (parameter.dataType === 'boolean' && typeof value === 'boolean') {
        return {
            ...parameter,
            value,
        };
    } else if (typeof value === 'number' && (parameter.dataType === 'float' || parameter.dataType === 'integer')) {
        return { ...parameter, value };
    }
    return parameter;
};

export const updateSelectedParameter = <T extends string | boolean | number>(
    configurableParameters: ConfigurableParametersTaskChain[],
    parameterId: string,
    ids: string[],
    value: T
): ConfigurableParametersTaskChain[] => {
    return configurableParameters.map((taskConfigParameters) => {
        const [taskId, componentId] = ids;
        if (taskConfigParameters.taskId !== taskId) {
            return taskConfigParameters;
        }
        return {
            ...taskConfigParameters,
            components: taskConfigParameters.components.map((component) => {
                if (component.id !== componentId) {
                    return component;
                }
                if (ids.length === NUMBER_OF_CONCATENATED_IDS_WITH_GROUPS) {
                    return {
                        ...component,
                        groups: component.groups?.map((group) => {
                            const [, , groupId] = ids;
                            if (group.id === groupId) {
                                return {
                                    ...group,
                                    parameters: group.parameters.map((parameter) => {
                                        if (parameter.id === parameterId) {
                                            return getNewParameterValue(parameter, value);
                                        }
                                        return parameter;
                                    }),
                                };
                            }
                            return group;
                        }),
                    };
                }
                return {
                    ...component,
                    parameters: component.parameters?.map((parameter) => {
                        if (parameter.id === parameterId) {
                            return getNewParameterValue(parameter, value);
                        }
                        return parameter;
                    }),
                };
            }),
        };
    });
};

export const getReconfigureParametersDTO = (
    configParameters: ConfigurableParametersTaskChain[]
): ConfigurableParametersReconfigureDTO => {
    const [globalEntity] = configParameters.filter(({ taskId }) => taskId === 'global-config');
    const global: ConfigurableParametersReconfigureDTO['global'] = getConfigGlobalDTO(globalEntity);

    const taskChainEntity = configParameters.filter(({ taskId }) => taskId !== 'global-config');
    const task_chain: ConfigurableParametersReconfigureDTO['task_chain'] = getConfigTaskChainDTO(taskChainEntity);

    return {
        global,
        task_chain,
    };
};

const getEntityIdentifierDTO = (entityIdentifier: EntityIdentifier): EntityIdentifierDTO => {
    if (entityIdentifier.type === 'HYPER_PARAMETER_GROUP') {
        const { type, modelStorageId, workspaceId, groupName } = entityIdentifier;
        return {
            type,
            model_storage_id: modelStorageId,
            workspace_id: workspaceId,
            group_name: groupName,
        };
    } else if (entityIdentifier.type === 'HYPER_PARAMETERS') {
        const { type, modelStorageId, workspaceId } = entityIdentifier;
        return {
            type,
            model_storage_id: modelStorageId,
            workspace_id: workspaceId,
        };
    }
    if (entityIdentifier.taskId) {
        return {
            task_id: entityIdentifier.taskId,
            type: entityIdentifier.type,
            project_id: entityIdentifier.projectId,
            workspace_id: entityIdentifier.workspaceId,
            component: entityIdentifier.component,
        };
    }
    return {
        type: entityIdentifier.type,
        project_id: entityIdentifier.projectId,
        workspace_id: entityIdentifier.workspaceId,
        component: entityIdentifier.component,
    };
};

const getConfigTaskChainDTO = (
    taskChain: ConfigurableParametersTaskChain[]
): ConfigurableParametersReconfigureDTO['task_chain'] =>
    taskChain.map(({ components }) => ({
        components: getComponentsDTO(components),
    }));

const getConfigGlobalDTO = (global: ConfigurableParametersTaskChain): ConfigurableParametersReconfigureDTO['global'] =>
    global.components.map(({ parameters, entityIdentifier }) => {
        return {
            type: 'CONFIGURABLE_PARAMETERS',
            parameters: getParametersDTO(parameters),
            entity_identifier: getEntityIdentifierDTO(entityIdentifier),
        };
    });

const getParametersDTO = (parameters?: ConfigurableParametersParams[]): ConfigurableParametersParamsReconfigureDTO[] =>
    parameters?.map(({ value, name }) => ({ value, name })) ?? [];

const hasComponentOnlyGroupsDTO = (
    groups: ConfigurableParametersGroups[]
): ConfigurableParametersComponentsBodyDTO['groups'] =>
    groups.map(({ parameters, type, name }) => ({
        type,
        name,
        parameters: getParametersDTO(parameters),
    }));

export const getComponentsDTO = (
    components: ConfigurableParametersComponents[]
): ConfigurableParametersComponentsBodyDTO[] =>
    components.map((component) => {
        const groups = isNonEmptyArray(component.groups) ? hasComponentOnlyGroupsDTO(component.groups) : undefined;
        const parameters = isNonEmptyArray(component.parameters) ? getParametersDTO(component.parameters) : undefined;
        return {
            entity_identifier: getEntityIdentifierDTO(component.entityIdentifier),
            groups,
            parameters,
        };
    });
