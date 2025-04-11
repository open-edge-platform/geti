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

import { ButtonProps } from '../../shared/components/button/button.component';
import { WorkspaceIdentifier } from '../workspaces/services/workspaces.interface';
import {
    DATASET_IMPORT_DIALOG_BUTTONS,
    DATASET_IMPORT_TASK_TYPE,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
    DATASET_IMPORT_WARNING_TYPE,
} from './dataset.enum';

export interface DatasetImport {
    id: string;
}

export interface DatasetImportIdentifier extends WorkspaceIdentifier {
    uploadId: string;
    setAbortController: (uploadId: string, abortController: AbortController) => void;
}

export interface DatasetImportWarning {
    type: DATASET_IMPORT_WARNING_TYPE;
    name: string;
    description: string;
    affectedImages?: number;
    resolveStrategy?: string;
}

export interface DatasetImportItem extends DatasetImport {
    name: string;
    size: string;
    status: string;
    progress: number;
    startAt: number;
    startFromBytes: number;
    uploadId: string | null;
    bytesRemaining: string | null;
    timeRemaining: string | null;
    preparingJobId?: string | null;
    importingJobId?: string | null;
    warnings: DatasetImportWarning[];
}

export interface DatasetImportDialogButton {
    name: DATASET_IMPORT_DIALOG_BUTTONS;
    hidden: boolean;
    disabled: boolean;
    variant: ButtonProps['variant'];
    action?: () => void;
}

export interface DatasetImportLabel {
    name: string;
    color?: string;
    group?: string | null;
    parent?: string | null;
}

// Dataset Import to new project

export interface DatasetImportProjectData {
    uploadId: string;
    projectName: string;
    taskType: DATASET_IMPORT_TASK_TYPE;
    labels: { name: string; color: string }[];
}

export interface DatasetImportToNewProjectIdentifier {
    organizationId: string;
    workspaceId: string;
    projectData: DatasetImportProjectData;
    setAbortController: (uploadId: string, abortController: AbortController) => void;
    anomalyRevamp: boolean;
}

export interface DatasetImportTask {
    title: string;
    taskType: DATASET_IMPORT_TASK_TYPE;
    labels: DatasetImportLabel[];
}

export interface DatasetImportConnection {
    from: string;
    to: string;
}

export interface DatasetImportPipeline {
    tasks: DatasetImportTask[];
    connections: DatasetImportConnection[];
}

export interface DatasetImportSupportedProjectType {
    projectType: string;
    pipeline: DatasetImportPipeline;
}

export interface DatasetImportPrepareForNewProjectResponse {
    warnings: DatasetImportWarning[];
    supportedProjectTypes: DatasetImportSupportedProjectType[];
}

export interface DatasetImportToNewProjectResponse {
    projectId: string;
}

export interface DatasetImportToNewProjectItem extends DatasetImportItem {
    labels: DatasetImportLabel[]; // Labels that have been selected
    labelsToSelect: DatasetImportLabel[]; // Labels that are available
    firstChainTaskType: DATASET_IMPORT_TASK_TYPE | null; // First task type
    firstChainLabels: DatasetImportLabel[]; // First task labels for chained projects
    supportedProjectTypes: DatasetImportSupportedProjectType[];
    labelColorMap: Record<string, string>;
    activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP;
    openedSteps: DATASET_IMPORT_TO_NEW_PROJECT_STEP[];
    completedSteps: DATASET_IMPORT_TO_NEW_PROJECT_STEP[];
    projectName: string;
    taskType: DATASET_IMPORT_TASK_TYPE | null;
}

// Dataset Import to existing project

export interface DatasetImportToExistingProjectItem extends DatasetImportItem {
    projectId: string;
    datasetId: string;
    datasetName: string;
    labels: string[];
    labelsMap: Record<string, string>;
}

export interface DatasetPrepareForExistingProjectIdentifier extends DatasetImportIdentifier {
    projectId: string;
}

export interface DatasetImportToExistingProjectIdentifier extends DatasetPrepareForExistingProjectIdentifier {
    datasetId: string;
    datasetName: string;
    labelsMap: Record<string, string>;
}

export interface DatasetPrepareForExistingProjectResponse {
    warnings: DatasetImportWarning[];
    labels: string[];
}
