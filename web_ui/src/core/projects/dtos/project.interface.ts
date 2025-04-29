// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
