// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { LifecycleStage } from '../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';

export enum ModelConfigurationOption {
    LATEST_CONFIGURATION = 'LATEST_CONFIGURATION',
    MANUAL_CONFIGURATION = 'MANUAL_CONFIGURATION',
}

export const LATEST_MODEL_CONFIG_TOOLTIP_TEXT =
    'The system will use the latest model configurable parameters ' +
    'for the training, in case no model trained for this architecture before, ' +
    'the system will use the default configurable parameters.';

export const CUSTOM_MODEL_CONFIG_TOOLTIP_TEXT =
    'Currently only facilitates training of the existing pre-defined architectures ' +
    'with custom training parameters.';

export const isDeprecatedAlgorithm = (lifecycleStage: LifecycleStage) => lifecycleStage === LifecycleStage.DEPRECATED;

export const isObsoleteAlgorithm = (lifecycleStage: LifecycleStage) => lifecycleStage === LifecycleStage.OBSOLETE;
