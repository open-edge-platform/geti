// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceIdentifier } from '../../../../packages/core/src/workspaces/services/workspaces.interface';
import {
    JobImportDatasetToExistingProjectStatus,
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
    JobPrepareDatasetToExistingProjectStatus,
    JobStatusIdentifier,
} from '../../jobs/jobs.interface';
import { CreateDatasetResponse } from '../../projects/dataset.interface';
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
