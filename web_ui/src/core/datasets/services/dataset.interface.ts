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

import {
    JobImportDatasetToExistingProjectStatus,
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
    JobPrepareDatasetToExistingProjectStatus,
    JobStatusIdentifier,
} from '../../jobs/jobs.interface';
import { CreateDatasetResponse } from '../../projects/dataset.interface';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import {
    DatasetImportIdentifier,
    DatasetImportPrepareForNewProjectResponse,
    DatasetImportToExistingProjectIdentifier,
    DatasetImportToNewProjectIdentifier,
    DatasetImportToNewProjectResponse,
    DatasetPrepareForExistingProjectIdentifier,
    DatasetPrepareForExistingProjectResponse,
} from '../dataset.interface';

export interface DatasetImportService {
    prepareDatasetForNewProject({
        workspaceId,
        uploadId,
        setAbortController,
    }: DatasetImportIdentifier): Promise<DatasetImportPrepareForNewProjectResponse>;

    prepareDatasetJob({ workspaceId, uploadId, setAbortController }: DatasetImportIdentifier): Promise<{
        jobId: string;
    }>;

    importDatasetToNewProject({
        workspaceId,
        projectData,
        setAbortController,
    }: DatasetImportToNewProjectIdentifier): Promise<DatasetImportToNewProjectResponse>;

    importDatasetToNewProjectJob({
        workspaceId,
        projectData,
        setAbortController,
    }: DatasetImportToNewProjectIdentifier): Promise<{ jobId: string }>;

    prepareDatasetToExistingProject({
        workspaceId,
        uploadId,
        projectId,
        setAbortController,
    }: DatasetPrepareForExistingProjectIdentifier): Promise<DatasetPrepareForExistingProjectResponse>;

    prepareDatasetToExistingProjectJob({
        workspaceId,
        uploadId,
        projectId,
        setAbortController,
    }: DatasetPrepareForExistingProjectIdentifier): Promise<{ jobId: string }>;

    importDatasetToExistingProject({
        workspaceId,
        uploadId,
        projectId,
        labelsMap,
        setAbortController,
    }: DatasetImportToExistingProjectIdentifier): Promise<CreateDatasetResponse>;

    importDatasetToExistingProjectJob({
        workspaceId,
        uploadId,
        projectId,
        labelsMap,
        setAbortController,
    }: DatasetImportToExistingProjectIdentifier): Promise<{ jobId: string }>;

    importDatasetToExistingProjectStatusJob: ({
        jobId,
        workspaceId,
        organizationId,
    }: JobStatusIdentifier) => Promise<JobImportDatasetToExistingProjectStatus>;

    prepareDatasetImportNewProjectJob(data: JobStatusIdentifier): Promise<JobPrepareDatasetImportNewProjectStatus>;
    importDatasetToNewProjectStatusJob(data: JobStatusIdentifier): Promise<JobImportDatasetToNewProjectStatus>;
    prepareDatasetToExistingProjectStatusJob(
        data: JobStatusIdentifier
    ): Promise<JobPrepareDatasetToExistingProjectStatus>;

    deleteImportProjectFromDataset(workspaceIdentifier: WorkspaceIdentifier & { fileId: string }): Promise<void>;
}
