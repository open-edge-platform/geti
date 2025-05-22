// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import {
    BooleanGroupParamsDTO,
    ConfigGroupParametersDataTypesDTO,
    ConfigurableParametersComponentsDTO,
    ConfigurableParametersGroupsDTO,
    ConfigurableParametersTaskChainDTO,
    EntityIdentifierHyperDTO,
    EntityIdentifierHyperGroupDTO,
    EntityModelIdentifierDTO,
    EntityTaskIdentifierDTO,
    NumberGroupParamsDTO,
    SelectableGroupParamsDTO,
} from '../dtos/configurable-parameters.interface';

interface ConfigParametersId {
    id: string;
}

export interface SelectableGroupParams<T extends string | number, K extends ConfigGroupParametersDataTypesDTO>
    extends ConfigParametersId,
        Omit<SelectableGroupParamsDTO<T, K>, 'template_type' | 'data_type' | 'default_value'> {
    templateType: SelectableGroupParamsDTO<T, K>['template_type'];
    dataType: SelectableGroupParamsDTO<T, K>['data_type'];
    defaultValue: SelectableGroupParamsDTO<T, K>['default_value'];
}

export interface NumberGroupParams
    extends ConfigParametersId,
        Omit<NumberGroupParamsDTO, 'template_type' | 'data_type' | 'min_value' | 'max_value' | 'default_value'> {
    templateType: NumberGroupParamsDTO['template_type'];
    dataType: NumberGroupParamsDTO['data_type'];
    minValue: NumberGroupParamsDTO['min_value'];
    maxValue: NumberGroupParamsDTO['max_value'];
    defaultValue: NumberGroupParamsDTO['default_value'];
}

export interface BooleanGroupParams
    extends ConfigParametersId,
        Omit<BooleanGroupParamsDTO, 'template_type' | 'data_type' | 'default_value'> {
    templateType: BooleanGroupParamsDTO['template_type'];
    dataType: BooleanGroupParamsDTO['data_type'];
    defaultValue: BooleanGroupParamsDTO['default_value'];
}

export type ConfigurableParametersParams =
    | SelectableGroupParams<string, 'string'>
    | SelectableGroupParams<number, 'integer' | 'float'>
    | BooleanGroupParams
    | NumberGroupParams;

export interface ConfigurableParametersGroups extends Omit<ConfigurableParametersGroupsDTO, 'parameters'> {
    id: string;
    parameters: ConfigurableParametersParams[];
}

interface EntityIdentifierGenericModel {
    modelStorageId: EntityModelIdentifierDTO['model_storage_id'];
    workspaceId: EntityModelIdentifierDTO['workspace_id'];
}

export interface EntityIdentifierHyperGroup
    extends Pick<EntityIdentifierHyperGroupDTO, 'type'>,
        EntityIdentifierGenericModel {
    groupName: EntityIdentifierHyperGroupDTO['group_name'];
}

type EntityIdentifierHyper = Pick<EntityIdentifierHyperDTO, 'type'> & EntityIdentifierGenericModel;

export type EntityModelIdentifier = EntityIdentifierHyperGroup | EntityIdentifierHyper;

export interface EntityTaskIdentifier extends Pick<EntityTaskIdentifierDTO, 'type' | 'component'> {
    workspaceId: EntityTaskIdentifierDTO['workspace_id'];
    taskId: EntityTaskIdentifierDTO['task_id'];
    projectId: EntityTaskIdentifierDTO['project_id'];
}

export type EntityIdentifier = EntityModelIdentifier | EntityTaskIdentifier;

export interface ConfigurableParametersComponents
    extends Omit<ConfigurableParametersComponentsDTO, 'groups' | 'parameters' | 'entity_identifier'> {
    entityIdentifier: EntityIdentifier;
    groups?: ConfigurableParametersGroups[];
    parameters?: ConfigurableParametersParams[];
}

export interface ConfigurableParametersTaskChain {
    taskId: ConfigurableParametersTaskChainDTO['task_id'];
    taskTitle: ConfigurableParametersTaskChainDTO['task_title'];
    components: ConfigurableParametersComponents[];
}

export enum ConfigurableParametersType {
    SINGLE_CONFIG_PARAMETERS = 'single-config-parameters',
    MANY_CONFIG_PARAMETERS = 'many-config-parameters',
    READ_ONLY_SINGLE_PARAMETERS = 'read-only-single-parameters',
}

export interface ConfigurableParametersSingle {
    type: ConfigurableParametersType.SINGLE_CONFIG_PARAMETERS;
    configParametersData: ConfigurableParametersTaskChain;
    updateParameter<T extends string | boolean | number>(id: string, value: T): void;
}

interface ConfigurableParametersSingleReadOnly {
    type: ConfigurableParametersType.READ_ONLY_SINGLE_PARAMETERS;
    configParametersData: ConfigurableParametersTaskChain;
}

export interface ConfigurableParametersMany {
    type: ConfigurableParametersType.MANY_CONFIG_PARAMETERS;
    configParametersData: ConfigurableParametersTaskChain[];
    updateParameter: ConfigurableParametersSingle['updateParameter'];
    selectedComponentId: string | undefined;
    setSelectedComponentId: Dispatch<SetStateAction<string | undefined>>;
    selectedComponent: ConfigurableParametersComponents | undefined;
}

export type ConfigurableParametersProps =
    | ConfigurableParametersSingle
    | ConfigurableParametersSingleReadOnly
    | ConfigurableParametersMany;

export interface ConfigParameterItemProp {
    updateParameter?: ConfigurableParametersSingle['updateParameter'];
}
