// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface ParameterBase {
    key: string;
    name: string;
    description: string;
}

export interface NumberParameter extends ParameterBase {
    type: 'int' | 'float';
    value: number;
    minValue: number;
    maxValue: number;
    defaultValue: number;
}

export interface BoolParameter extends ParameterBase {
    type: 'bool';
    value: boolean;
    defaultValue: boolean;
}

interface EnumParameter extends ParameterBase {
    type: 'enum';
    value: string;
    defaultValue: string;
    allowedValues: string[];
}

export interface StaticParameter extends ParameterBase {
    value: number | string | boolean;
}

export type ConfigurationParameter = BoolParameter | NumberParameter | EnumParameter;

interface ProjectConfigurationTaskConfigsTraining {
    constraints: ConfigurationParameter[];
}

interface ProjectConfigurationTaskConfigs {
    taskId: string;
    training: ProjectConfigurationTaskConfigsTraining;
    autoTraining: ConfigurationParameter[];
}

export type KeyValueParameter = Pick<ConfigurationParameter, 'key' | 'value'>;

export interface ProjectConfigurationUploadPayload {
    taskConfigs: {
        taskId: string;
        training?: {
            constraints: KeyValueParameter[];
        };
        autoTraining?: KeyValueParameter[];
    }[];
}

export interface ProjectConfiguration {
    taskConfigs: ProjectConfigurationTaskConfigs[];
}

export type DatasetPreparationParameters = {
    subsetSplit: ConfigurationParameter[];
    filtering: Record<string, ConfigurationParameter[]>;
    augmentation: Record<string, ConfigurationParameter[]>;
};

export type TrainingParameters = ConfigurationParameter[] | Record<string, ConfigurationParameter[]>[];

export interface TrainingConfiguration {
    datasetPreparation: DatasetPreparationParameters;
    training: TrainingParameters;
    evaluation: ConfigurationParameter[];
    advancedConfiguration?: StaticParameter[];
    taskId: string;
}

export interface TrainingConfigurationUpdatePayload {
    datasetPreparation?: Record<string, KeyValueParameter[]>;
    training?: KeyValueParameter[];
    evaluation?: KeyValueParameter[];
    advancedConfiguration?: KeyValueParameter[];
}
