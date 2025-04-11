// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { TASK_TYPE } from '../../projects/dtos/task.interface';

export enum PerformanceCategory {
    OTHER = 'other',
    SPEED = 'speed',
    BALANCE = 'balance',
    ACCURACY = 'accuracy',
}

export enum LifecycleStage {
    ACTIVE = 'active',
    OBSOLETE = 'obsolete',
    DEPRECATED = 'deprecated',
}

export interface SupportedAlgorithmDTO {
    name: string;
    model_size: number;
    gigaflops: number;
    task_type: TASK_TYPE;
    model_template_id: string;
    summary: string;
    default_algorithm: boolean;
    lifecycle_stage: LifecycleStage;
    performance_category: PerformanceCategory;
}

export interface SupportedAlgorithmsResponseDTO {
    supported_algorithms: SupportedAlgorithmDTO[];
}
