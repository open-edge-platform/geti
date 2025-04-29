// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
