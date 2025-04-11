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

import { KeypointTaskDTO, TaskDTO } from './task.interface';

export interface ConnectionDTO {
    from: string;
    to: string;
}

export interface ProjectCommon {
    name: string;
}

export interface DatasetDTO {
    id: string;
    name: string;
    creation_time: string;
    use_for_training: boolean;
}

export interface ScoreDTO {
    value: number;
    metric_type: string;
}

interface TaskPerformanceDTO {
    task_id: string;
    score: ScoreDTO | null;
    global_score?: ScoreDTO | null;
    local_score?: ScoreDTO | null;
}

export interface PerformanceDTO {
    score: number | null;
    global_score?: number | null;
    local_score?: number | null;
    task_performances: TaskPerformanceDTO[];
}

export interface ProjectDTO extends ProjectCommon {
    creation_time: string;
    id: string;
    name: string;
    datasets: DatasetDTO[];
    pipeline: {
        connections: ConnectionDTO[];
        tasks: TaskDTO[] | KeypointTaskDTO[];
    };
    performance: PerformanceDTO;
    thumbnail: string;
    storage_info?: { size: number } | Record<string, never>;
}

//Note: we don't want to send storage_info while project edition
export type EditProjectDTO = Omit<ProjectDTO, 'storage_info'>;
