// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ProjectStatusTaskDTO } from './dtos/status.interface';
import { Performance } from './task.interface';

export interface RequiredAnnotationsDetailsEntry {
    id: string;
    name: string;
    color: string;
    value: number;
}

export interface ProjectStatus {
    performance: Performance;
    isTraining: boolean;
    trainingDetails?: { progress: string; timeRemaining?: string };
    tasks: ProjectStatusTaskDTO[];
}
