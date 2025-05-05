// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface ParameterBase {
    key: string;
    name: string;
    description: string;
}

interface NumberParameter extends ParameterBase {
    type: 'int' | 'float';
    value: number;
    minValue: number;
    maxValue: number;
    defaultValue: number;
}

interface BoolParameter extends ParameterBase {
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

interface StaticParameter extends ParameterBase {
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
    predictions: ConfigurationParameter[];
}

export interface ProjectConfiguration {
    taskConfigs: ProjectConfigurationTaskConfigs[];
}

export type TrainingConfiguration =
    | Record<string, Record<string, ConfigurationParameter[]> | ConfigurationParameter[]>
    | { advancedConfiguration: StaticParameter[] };
