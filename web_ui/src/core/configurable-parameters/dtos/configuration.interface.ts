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
}

type KeyValueParameterDTO = Pick<ConfigurationParameterDTO, 'key' | 'value'>;

export interface ProjectConfigurationUploadPayloadDTO {
    task_configs: {
        task_id: string;
        training?: { constraints: KeyValueParameterDTO[] };
        auto_training?: KeyValueParameterDTO[];
    }[];
}

export interface ProjectConfigurationDTO {
    task_configs: ProjectConfigurationTaskConfigsDTO[];
}

export type DatasetPreparationParametersDTO = {
    subset_split: ConfigurationParameterDTO[];
    filtering: Record<string, ConfigurationParameterDTO[]>;
    augmentation: Record<string, ConfigurationParameterDTO[]>;
};

export type TrainingParametersDTO = ConfigurationParameterDTO[] | Record<string, ConfigurationParameterDTO[]>[];

export interface TrainingConfigurationDTO {
    dataset_preparation: DatasetPreparationParametersDTO;
    training: TrainingParametersDTO;
    evaluation: ConfigurationParameterDTO[];
    advanced_configuration?: StaticParameterDTO[];
    task_id: string;
}

export interface TrainingConfigurationUpdatePayloadDTO {
    dataset_preparation?: Record<string, KeyValueParameterDTO[]>;
    training?: KeyValueParameterDTO[];
    evaluation?: KeyValueParameterDTO[];
    advanced_configuration?: KeyValueParameterDTO[];
}
