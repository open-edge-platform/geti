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
