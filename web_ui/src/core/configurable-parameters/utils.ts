// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEqual } from 'lodash-es';

import { isNonEmptyArray } from '../../shared/utils';
import {
    ConfigurableParametersComponentsBodyDTO,
    ConfigurableParametersParamsReconfigureDTO,
    ConfigurableParametersReconfigureDTO,
    EntityIdentifierDTO,
} from './dtos/configurable-parameters.interface';
import {
    BooleanGroupParams,
    ConfigurableParametersComponents,
    ConfigurableParametersGroups,
    ConfigurableParametersParams,
    ConfigurableParametersTaskChain,
    EntityIdentifier,
    NumberGroupParams,
} from './services/configurable-parameters.interface';

const hasEqualHeader =
    <T extends { header: string }>(toFind: string | null | undefined) =>
    ({ header }: T) =>
        isEqual(toFind, header);

const getConfigByTaskId = (taskId: string) => (task: ConfigurableParametersTaskChain) => taskId === task.taskId;

/**
 * @deprecated
 */
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

/**
 * @deprecated
 */
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

/**
 * @deprecated
 */
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

const NUMBER_OF_CONCATENATED_IDS_WITH_GROUPS = 4; // taskId::componentId::groupId::parameterId

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

const getConfigTaskChainDTO = (
    taskChain: ConfigurableParametersTaskChain[]
): ConfigurableParametersReconfigureDTO['task_chain'] =>
    taskChain.map(({ components }) => ({
        components: getComponentsDTO(components),
    }));

export const getParametersDTO = (
    parameters?: ConfigurableParametersParams[]
): ConfigurableParametersParamsReconfigureDTO[] => parameters?.map(({ value, name }) => ({ value, name })) ?? [];

export const getEntityIdentifierDTO = (entityIdentifier: EntityIdentifier): EntityIdentifierDTO => {
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

const getConfigGlobalDTO = (global: ConfigurableParametersTaskChain): ConfigurableParametersReconfigureDTO['global'] =>
    global.components.map(({ parameters, entityIdentifier }) => {
        return {
            type: 'CONFIGURABLE_PARAMETERS',
            parameters: getParametersDTO(parameters),
            entity_identifier: getEntityIdentifierDTO(entityIdentifier),
        };
    });

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
