// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface ParameterBaseDTO {
    key: string;
    name: string;
    description: string;
}

interface NumberParameterDTO extends ParameterBaseDTO {
    type: 'int' | 'float';
    value: number;
    min_value: number;
    max_value: number;
    default_value: number;
}

interface BoolParameterDTO extends ParameterBaseDTO {
    type: 'bool';
    value: boolean;
    default_value: boolean;
}

interface EnumParameterDTO extends ParameterBaseDTO {
    type: 'enum';
    value: string;
    default_value: string;
    allowed_values: string[];
}

export interface StaticParameterDTO extends ParameterBaseDTO {
    value: number | string | boolean;
}

export type ConfigurationParameterDTO = BoolParameterDTO | NumberParameterDTO | EnumParameterDTO;

interface ProjectConfigurationTaskConfigsTrainingDTO {
    constraints: ConfigurationParameterDTO[];
}

interface ProjectConfigurationTaskConfigsDTO {
    task_id: string;
    training: ProjectConfigurationTaskConfigsTrainingDTO;
    auto_training: ConfigurationParameterDTO[];
    predictions: ConfigurationParameterDTO[];
}

type KeyValueParameterDTO = Pick<ConfigurationParameterDTO, 'key' | 'value'>;

export interface ProjectConfigurationUploadPayloadDTO {
    training?: { constraints: KeyValueParameterDTO[] };
    auto_training?: KeyValueParameterDTO[];
    predictions?: KeyValueParameterDTO[];
}

export interface ProjectConfigurationDTO {
    task_configs: ProjectConfigurationTaskConfigsDTO[];
}

export interface TrainingConfigurationDTO {
    dataset_preparation: Record<string, ConfigurationParameterDTO[]>;
    training: ConfigurationParameterDTO[];
    evaluation: ConfigurationParameterDTO[];
    advanced_configuration?: StaticParameterDTO[];
}

export interface TrainingConfigurationUpdatePayloadDTO {
    dataset_preparation?: Record<string, KeyValueParameterDTO[]>;
    training?: KeyValueParameterDTO[];
    evaluation?: KeyValueParameterDTO[];
    advanced_configuration?: KeyValueParameterDTO[];
}
