// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface ConfigurableParametersBasicDTO {
    header: string;
    description: string;
    name: string;
}

type ConfigGroupParametersTemplateTypesDTO = 'selectable' | 'input';

export type ConfigGroupParametersDataTypesDTO = 'string' | 'integer' | 'float' | 'boolean';

interface ConfigurableParametersGroupBasicParamsDTO extends ConfigurableParametersBasicDTO {
    warning: string | null;
    editable: boolean;
}

export interface SelectableGroupParamsDTO<T extends string | number, K extends ConfigGroupParametersDataTypesDTO>
    extends ConfigurableParametersGroupBasicParamsDTO {
    template_type: Extract<ConfigGroupParametersTemplateTypesDTO, 'selectable'>;
    data_type: K;
    options: T[];
    value: T;
    default_value: T;
}

export interface BooleanGroupParamsDTO extends ConfigurableParametersGroupBasicParamsDTO {
    template_type: ConfigGroupParametersTemplateTypesDTO;
    data_type: Extract<ConfigGroupParametersDataTypesDTO, 'boolean'>;
    value: boolean;
    default_value: boolean;
}

export interface NumberGroupParamsDTO extends ConfigurableParametersGroupBasicParamsDTO {
    template_type: Extract<ConfigGroupParametersTemplateTypesDTO, 'input'>;
    data_type: Extract<ConfigGroupParametersDataTypesDTO, 'integer' | 'float'>;
    min_value: number;
    max_value: number;
    value: number;
    default_value: number;
}

export type ConfigurableParametersParamsDTO =
    | SelectableGroupParamsDTO<string, 'string'>
    | SelectableGroupParamsDTO<number, 'integer' | 'float'>
    | BooleanGroupParamsDTO
    | NumberGroupParamsDTO;

export interface ConfigurableParametersGroupsDTO extends ConfigurableParametersBasicDTO {
    type: 'PARAMETER_GROUP';
    parameters: ConfigurableParametersParamsDTO[];
}

interface EntityIdentifierGenericModelDTO {
    workspace_id: string;
    model_storage_id: string;
}

export interface EntityIdentifierHyperGroupDTO extends EntityIdentifierGenericModelDTO {
    type: 'HYPER_PARAMETER_GROUP';
    group_name: string;
}

export interface EntityIdentifierHyperDTO extends EntityIdentifierGenericModelDTO {
    type: 'HYPER_PARAMETERS';
}

export type EntityModelIdentifierDTO = EntityIdentifierHyperGroupDTO | EntityIdentifierHyperDTO;

export interface EntityTaskIdentifierDTO {
    workspace_id: string;
    project_id: string;
    component: string;
    task_id?: string;
    type: 'COMPONENT_PARAMETERS';
}

export type EntityIdentifierDTO = EntityModelIdentifierDTO | EntityTaskIdentifierDTO;

export interface ConfigurableParametersComponentsDTO extends Omit<ConfigurableParametersBasicDTO, 'name'> {
    id: string;
    entity_identifier: EntityIdentifierDTO;
    groups?: ConfigurableParametersGroupsDTO[];
    parameters?: ConfigurableParametersParamsDTO[];
}

export interface ConfigurableParametersTaskChainDTO {
    task_id: string;
    task_title: string;
    components: ConfigurableParametersComponentsDTO[];
}

interface ConfigurableParametersGlobalDTO extends Omit<ConfigurableParametersBasicDTO, 'name'> {
    id: string;
    type: 'CONFIGURABLE_PARAMETERS';
    entity_identifier: EntityIdentifierDTO;
    parameters: ConfigurableParametersParamsDTO[];
}

export interface ConfigurableParametersDTO {
    global: ConfigurableParametersGlobalDTO[];
    task_chain: ConfigurableParametersTaskChainDTO[];
}

export interface ConfigurableParametersParamsReconfigureDTO {
    name: ConfigurableParametersParamsDTO['name'];
    value: ConfigurableParametersParamsDTO['value'];
}

export interface ConfigurableParametersComponentsBodyDTO {
    entity_identifier: EntityIdentifierDTO;
    groups?: {
        type: ConfigurableParametersGroupsDTO['type'];
        name: ConfigurableParametersGroupsDTO['name'];
        parameters: ConfigurableParametersParamsReconfigureDTO[];
    }[];
    parameters?: ConfigurableParametersParamsReconfigureDTO[];
}

export interface ConfigurableParametersReconfigureDTO {
    global: {
        entity_identifier: EntityIdentifierDTO;
        parameters: ConfigurableParametersParamsReconfigureDTO[];
        type: ConfigurableParametersGlobalDTO['type'];
    }[];
    task_chain: {
        components: ConfigurableParametersComponentsBodyDTO[];
    }[];
}

export enum ExportStatusStateDTO {
    DONE = 'DONE',
    ERROR = 'ERROR',
    ZIPPING = 'ZIPPING',
    STARTING = 'STARTING',
    EXPORTING = 'EXPORTING',
}

export interface ExportDatasetStatusDTO {
    state: ExportStatusStateDTO;
    message: string;
    progress: number;
    download_url: string;
}
