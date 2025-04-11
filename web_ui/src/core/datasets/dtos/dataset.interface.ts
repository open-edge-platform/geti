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

import { CreateDatasetResponseDTO } from '../../projects/dataset.interface';
import { DATASET_IMPORT_WARNING_TYPE } from '../dataset.enum';
import { DATASET_IMPORT_TASK_TYPE_DTO } from './dataset.enum';

// Dataset Import

export interface DatasetImportWarningDTO {
    type: DATASET_IMPORT_WARNING_TYPE;
    name: string;
    description: string;
    affected_images?: number;
    resolve_strategy?: string;
}

// Dataset Import for new project

export interface DatasetImportLabelDTO {
    name: string;
    color?: string;
    group?: string | null;
    parent?: string | null;
}

export interface DatasetImportTaskDTO {
    title: string;
    task_type: DATASET_IMPORT_TASK_TYPE_DTO;
    labels: DatasetImportLabelDTO[];
}

export interface DatasetImportConnectionDTO {
    from: string;
    to: string;
}

export interface DatasetImportPipelineDTO {
    tasks: DatasetImportTaskDTO[];
    connections: DatasetImportConnectionDTO[];
}

export interface DatasetImportSupportedProjectTypeDTO {
    project_type: string;
    pipeline: DatasetImportPipelineDTO;
}

export interface DatasetImportPrepareForNewProjectResponseDTO {
    warnings: DatasetImportWarningDTO[];
    supported_project_types: DatasetImportSupportedProjectTypeDTO[];
}

export interface DatasetImportToNewProjectPayloadDTO {
    file_id: string;
    project_name: string;
    task_type: string;
    labels: { name: string; color: string }[];
}

export interface DatasetImportToNewProjectResponseDTO {
    project_id: string;
}

// Dataset Import to existing project

export interface DatasetPrepareForExistingProjectResponseDTO {
    warnings: DatasetImportWarningDTO[];
    labels: string[];
}

export interface DatasetImportToExistingProjectResponseDTO {
    dataset: CreateDatasetResponseDTO;
}
