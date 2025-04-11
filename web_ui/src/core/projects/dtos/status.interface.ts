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
