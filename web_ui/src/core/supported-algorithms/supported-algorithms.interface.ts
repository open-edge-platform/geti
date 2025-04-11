// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DOMAIN } from '../projects/core.interface';
import { SupportedAlgorithmDTO } from './dtos/supported-algorithms.interface';

export enum ModelTemplatesNames {
    ACCURACY = 'Accuracy',
    SPEED = 'Speed',
    BALANCE = 'Balance',
}

export interface SupportedAlgorithm {
    name: SupportedAlgorithmDTO['name'];
    modelSize: SupportedAlgorithmDTO['model_size'];
    modelTemplateId: SupportedAlgorithmDTO['model_template_id'];
    templateName: ModelTemplatesNames | undefined;
    domain: DOMAIN;
    summary: string;
    gigaflops: number;
    isDefaultAlgorithm: boolean;
    lifecycleStage: SupportedAlgorithmDTO['lifecycle_stage'];
    performanceCategory: SupportedAlgorithmDTO['performance_category'];
    license: string;
}

export type TaskWithSupportedAlgorithms = Record<string, SupportedAlgorithm[]>;
