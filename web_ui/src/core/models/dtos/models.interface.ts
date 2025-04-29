// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { LifecycleStage } from '../../supported-algorithms/dtos/supported-algorithms.interface';

export type ModelPerformanceDTO =
    | { global_score: number | null; local_score: number | null }
    | { score: number | null };

export interface ModelDTO {
    id: string;
    name: string;
    creation_date: string;
    performance: ModelPerformanceDTO;
    size: number;
    active_model: boolean;
    version: number;
    label_schema_in_sync: boolean;
    total_disk_size: number;
    purge_info?: {
        user_uid: null | string;
        is_purged: boolean;
        purge_time: null | string;
    };
    lifecycle_stage: LifecycleStage;
}

export interface ModelGroupsDTO {
    model_groups: ModelsDTO[];
}

export interface ModelsDTO {
    id: string;
    name: string;
    task_id: string;
    model_template_id: string;
    models: ModelDTO[];
    lifecycle_stage: LifecycleStage;
}
