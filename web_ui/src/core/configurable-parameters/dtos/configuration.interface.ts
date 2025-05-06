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

export type ProjectConfigurationUploadPayloadDTO = {
    [K in keyof Pick<
        ProjectConfigurationTaskConfigsDTO,
        'training' | 'auto_training' | 'predictions'
    >]?: ProjectConfigurationTaskConfigsDTO[K] extends ConfigurationParameterDTO[]
        ? Pick<ConfigurationParameterDTO, 'key' | 'value'>[]
        : { [P in keyof ProjectConfigurationTaskConfigsDTO[K]]?: Pick<ConfigurationParameterDTO, 'key' | 'value'>[] };
};

export interface ProjectConfigurationDTO {
    task_configs: ProjectConfigurationTaskConfigsDTO[];
}

interface TrainingConfigurationBaseDTO {
    dataset_preparation: Record<string, ConfigurationParameterDTO[]>;
    training: ConfigurationParameterDTO[];
    evaluation: ConfigurationParameterDTO[];
}

export interface TrainingConfigurationDTO extends TrainingConfigurationBaseDTO {
    advanced_configuration?: StaticParameterDTO[];
}

export type TrainingConfigurationUpdatePayloadDTO = {
    [K in keyof TrainingConfigurationBaseDTO]?: TrainingConfigurationBaseDTO[K] extends ConfigurationParameterDTO[]
        ? Pick<ConfigurationParameterDTO, 'key' | 'value'>[]
        : Record<string, Pick<ConfigurationParameterDTO, 'key' | 'value'>[]>;
};
