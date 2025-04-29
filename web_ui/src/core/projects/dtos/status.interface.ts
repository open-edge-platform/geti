// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PerformanceDTO } from './project.interface';

interface ProjectStatusEntryDTO {
    progress: number;
    time_remaining: number;
}

export interface ProjectStatusRequiredAnnotationsDetailEntryDTO {
    id: string;
    label_name: string;
    label_color: string;
    value: number;
}

export interface ProjectStatusRequiredAnnotationsDTO {
    details: ProjectStatusRequiredAnnotationsDetailEntryDTO[];
    value: number;
}

export interface ProjectStatusTaskDTO {
    id: string;
    title: string;
    is_training: boolean;
    status: ProjectStatusEntryDTO;
    n_new_annotations: number;
    required_annotations: ProjectStatusRequiredAnnotationsDTO;
    ready_to_train: boolean;
}

export interface ProjectStatusDTO {
    is_training: boolean;
    n_required_annotations: number;
    project_performance: PerformanceDTO;
    status: ProjectStatusEntryDTO;
    tasks: ProjectStatusTaskDTO[];
}
