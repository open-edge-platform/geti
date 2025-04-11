// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DatasetImportIdentifier } from '../../core/datasets/dataset.interface';
import { ProjectIdentifier } from '../../core/projects/core.interface';
import { DatasetIdentifier, ExportDatasetStatusIdentifier } from '../../core/projects/dataset.interface';
import { ProjectExportIdentifier, ProjectImportIdentifier } from '../../core/projects/project.interface';
import { WorkspaceIdentifier } from '../../core/workspaces/services/workspaces.interface';

export const getMockedWorkspaceIdentifier = (
    workspaceIdentifier: Partial<WorkspaceIdentifier> = {}
): WorkspaceIdentifier => {
    return {
        workspaceId: 'workspace-id',
        organizationId: 'organization-id',
        ...workspaceIdentifier,
    };
};

export const getMockedProjectIdentifier = (projectIdentifier: Partial<ProjectIdentifier> = {}): ProjectIdentifier => {
    return {
        ...getMockedWorkspaceIdentifier(),
        projectId: 'project-id',
        ...projectIdentifier,
    };
};

export const getMockedDatasetIdentifier = (datasetIdentifier: Partial<DatasetIdentifier> = {}): DatasetIdentifier => {
    return {
        ...getMockedProjectIdentifier(),
        datasetId: 'dataset-id',
        ...datasetIdentifier,
    };
};

export const getMockedProjectImportIdentifier = (
    projectImportIdentifier: Partial<ProjectImportIdentifier>
): ProjectImportIdentifier => {
    const { importProjectId, ...rest } = projectImportIdentifier;
    const { projectId, ...workspaceIdentifier } = getMockedProjectIdentifier(rest);

    return {
        importProjectId: importProjectId ?? projectId,
        ...getMockedProjectIdentifier(workspaceIdentifier),
    };
};

export const getMockedProjectExportIdentifier = (
    projectExportIdentifier: Partial<ProjectExportIdentifier>
): ProjectExportIdentifier => {
    const { exportProjectId, ...projectIdentifier } = projectExportIdentifier;

    return {
        exportProjectId: exportProjectId ?? 'export-project-id',
        ...getMockedProjectIdentifier(projectIdentifier),
    };
};

export const getMockedDatasetExportIdentifier = (
    datasetExportIdentifier: Partial<ExportDatasetStatusIdentifier>
): ExportDatasetStatusIdentifier => {
    const { exportDatasetId, ...datasetIdentifier } = datasetExportIdentifier;
    return {
        ...getMockedDatasetIdentifier(datasetIdentifier),
        exportDatasetId: exportDatasetId ?? 'export-dataset-id',
    };
};

export const getMockedDatasetImportPayload = (
    datasetImportIdentifier: Partial<DatasetImportIdentifier>
): DatasetImportIdentifier => {
    return {
        ...getMockedWorkspaceIdentifier(),
        uploadId: 'upload-1',
        setAbortController: jest.fn(),
        ...datasetImportIdentifier,
    };
};
