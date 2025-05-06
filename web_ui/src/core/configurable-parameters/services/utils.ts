// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { v4 as uuidV4 } from 'uuid';

import {
    ConfigurableParametersComponents,
    ConfigurableParametersGroups,
    ConfigurableParametersParams,
    ConfigurableParametersTaskChain,
    EntityIdentifier,
} from '../../../shared/components/configurable-parameters/configurable-parameters.interface';
import {
    ConfigurableParametersDTO,
    ConfigurableParametersGroupsDTO,
    ConfigurableParametersParamsDTO,
    ConfigurableParametersTaskChainDTO,
    EntityIdentifierDTO,
} from '../dtos/configurable-parameters.interface';
import {
    ConfigurationParameterDTO,
    ProjectConfigurationDTO,
    StaticParameterDTO,
    TrainingConfigurationDTO,
    TrainingConfigurationUpdatePayloadDTO,
} from '../dtos/configuration.interface';
import {
    ConfigurationParameter,
    ProjectConfiguration,
    StaticParameter,
    TrainingConfiguration,
    TrainingConfigurationUpdatePayload,
} from './configuration.interface';

const getConfigParametersField = (
    parameters: ConfigurableParametersParamsDTO[],
    id: string,
    editable = false
): ConfigurableParametersParams[] =>
    parameters.map((parameter) => {
        const parameterId = `${id}::${uuidV4()}`;

        if (parameter.data_type === 'boolean') {
            const { data_type, default_value, template_type, ...rest } = parameter;
            return {
                ...rest,
                editable,
                id: parameterId,
                dataType: data_type,
                templateType: template_type,
                defaultValue: default_value,
            };
        }
        if (parameter.template_type === 'selectable') {
            if (parameter.data_type === 'string') {
                const { default_value, template_type, data_type, ...rest } = parameter;
                return {
                    ...rest,
                    editable,
                    id: parameterId,
                    dataType: data_type,
                    templateType: template_type,
                    defaultValue: default_value,
                };
            }
            const { default_value, template_type, data_type, ...rest } = parameter;
            return {
                ...rest,
                editable,
                id: parameterId,
                dataType: data_type,
                templateType: template_type,
                defaultValue: default_value,
            };
        } else if (parameter.template_type === 'input') {
            const { data_type, template_type, default_value, max_value, min_value, ...rest } = parameter;
            return {
                ...rest,
                editable,
                id: parameterId,
                dataType: data_type,
                templateType: template_type,
                defaultValue: default_value,
                minValue: min_value,
                maxValue: max_value,
            };
        }
        throw Error('This template type is not supported');
    });

const getConfigEntityIdentifier = (entityIdentifierDTO: EntityIdentifierDTO): EntityIdentifier => {
    if (entityIdentifierDTO.type === 'HYPER_PARAMETER_GROUP') {
        const { type, model_storage_id, workspace_id, group_name } = entityIdentifierDTO;
        return {
            type,
            modelStorageId: model_storage_id,
            workspaceId: workspace_id,
            groupName: group_name,
        };
    } else if (entityIdentifierDTO.type === 'HYPER_PARAMETERS') {
        const { type, model_storage_id, workspace_id } = entityIdentifierDTO;
        return {
            type,
            modelStorageId: model_storage_id,
            workspaceId: workspace_id,
        };
    }
    const { type, component, project_id, task_id, workspace_id } = entityIdentifierDTO;
    return {
        type,
        component,
        projectId: project_id,
        taskId: task_id,
        workspaceId: workspace_id,
    };
};

const hasComponentOnlyParameters = (
    parameters: ConfigurableParametersParamsDTO[],
    taskComponentId: string,
    editable: boolean
): ConfigurableParametersParams[] => {
    return getConfigParametersField(parameters, taskComponentId, editable);
};

const hasComponentOnlyGroups = (
    groups: ConfigurableParametersGroupsDTO[],
    taskComponentId: string,
    editable: boolean
): ConfigurableParametersGroups[] => {
    return groups.map((group) => {
        const groupId = uuidV4();
        const parameterIdPrefix = `${taskComponentId}::${groupId}`;
        const newParameters: ConfigurableParametersParams[] = getConfigParametersField(
            group.parameters,
            parameterIdPrefix,
            editable
        );
        return {
            ...group,
            id: groupId,
            parameters: newParameters,
        };
    });
};

export const getModelConfigEntity = (
    data: ConfigurableParametersTaskChainDTO,
    editable = false
): ConfigurableParametersTaskChain => {
    const { task_id, task_title, components } = data;
    const newComponents: ConfigurableParametersComponents[] = components.map((component) => {
        const { description, header, id, entity_identifier } = component;
        const taskComponentId = `${task_id}::${id}`;
        const entityIdentifier: EntityIdentifier = getConfigEntityIdentifier(entity_identifier);
        const groups = component.groups
            ? hasComponentOnlyGroups(component.groups, taskComponentId, editable)
            : undefined;
        const parameters = component.parameters
            ? hasComponentOnlyParameters(component.parameters, taskComponentId, editable)
            : undefined;
        return {
            id,
            header,
            description,
            entityIdentifier,
            parameters,
            groups,
        };
    });

    return {
        taskId: task_id,
        taskTitle: task_title,
        components: newComponents,
    };
};

export const getConfigParametersEntity = (data: ConfigurableParametersDTO): ConfigurableParametersTaskChain[] => {
    const { global, task_chain } = data;
    const taskChain: ConfigurableParametersTaskChain[] = task_chain.map((taskConfigParameter) =>
        getModelConfigEntity(taskConfigParameter, true)
    );

    const taskId = 'global-config';
    const newGlobal: ConfigurableParametersTaskChain = {
        taskId,
        taskTitle: 'Global',
        components: global.map(({ parameters, header, description, entity_identifier, id }) => ({
            id,
            header,
            description,
            entityIdentifier: getConfigEntityIdentifier(entity_identifier),
            type: 'PARAMETER_GROUP',
            name: header.toLowerCase().split(' ').join('-'),
            parameters: getConfigParametersField(parameters, `${taskId}::${id}`, true),
        })),
    };

    return [newGlobal, ...taskChain];
};

export const getParameter = (parameter: ConfigurationParameterDTO): ConfigurationParameter => {
    if (parameter.type === 'int' || parameter.type === 'float') {
        const { type, description, key, default_value, max_value, min_value, value, name } = parameter;

        return {
            key,
            type,
            name,
            value,
            description,
            defaultValue: default_value,
            maxValue: max_value,
            minValue: min_value,
        };
    }

    if (parameter.type === 'bool') {
        const { type, description, key, default_value, value, name } = parameter;

        return {
            key,
            type,
            name,
            value,
            description,
            defaultValue: default_value,
        };
    }

    if (parameter.type === 'enum') {
        const { key, type, name, description, value, default_value, allowed_values } = parameter;

        return {
            key,
            type,
            name,
            description,
            allowedValues: allowed_values,
            value,
            defaultValue: default_value,
        };
    }

    throw new Error(`${parameter.type} is not supported.`);
};

export const getStaticParameter = (parameter: StaticParameterDTO): StaticParameter => {
    const { key, name, description, value } = parameter;

    return {
        key,
        name,
        description,
        value,
    };
};

export const getProjectConfigurationEntity = ({ task_configs }: ProjectConfigurationDTO): ProjectConfiguration => {
    const taskConfigs = task_configs.map((taskConfig) => {
        const { task_id, training, auto_training, predictions } = taskConfig;

        return {
            taskId: task_id,
            training: {
                constraints: training.constraints.map(getParameter),
            },
            autoTraining: auto_training.map(getParameter),
            predictions: predictions.map(getParameter),
        };
    });
    return {
        taskConfigs,
    };
};

export const getTrainingConfigurationEntity = (config: TrainingConfigurationDTO): TrainingConfiguration => {
    const trainingConfiguration: TrainingConfiguration = {
        datasetPreparation: Object.entries(config.dataset_preparation).reduce((acc, [key, value]) => {
            const parameters = value.map(getParameter);
            return {
                ...acc,
                [key]: parameters,
            };
        }, {}),
        training: config.training.map(getParameter),
        evaluation: config.evaluation.map(getParameter),
    };

    if (config.advanced_configuration !== undefined) {
        trainingConfiguration.advancedConfiguration = config.advanced_configuration.map(getStaticParameter);
    }

    return trainingConfiguration;
};

export const getTrainingConfigurationUpdatePayloadDTO = (
    payload: TrainingConfigurationUpdatePayload
): TrainingConfigurationUpdatePayloadDTO => {
    const trainingConfigurationUpdatePayload: TrainingConfigurationUpdatePayloadDTO = {};

    if (payload.datasetPreparation !== undefined) {
        trainingConfigurationUpdatePayload.dataset_preparation = Object.entries(payload.datasetPreparation).reduce(
            (acc, [key, parameters]) => {
                return {
                    ...acc,
                    [key]: parameters.map((parameter) => ({
                        key: parameter.key,
                        value: parameter.value,
                    })),
                };
            },
            {}
        );
    }

    if (payload.training !== undefined) {
        trainingConfigurationUpdatePayload.training = payload.training.map((parameter) => ({
            key: parameter.key,
            value: parameter.value,
        }));
    }

    if (payload.evaluation !== undefined) {
        trainingConfigurationUpdatePayload.evaluation = payload.evaluation.map((parameter) => ({
            key: parameter.key,
            value: parameter.value,
        }));
    }

    return trainingConfigurationUpdatePayload;
};
