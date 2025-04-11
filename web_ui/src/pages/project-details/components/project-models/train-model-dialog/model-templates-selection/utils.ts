// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
