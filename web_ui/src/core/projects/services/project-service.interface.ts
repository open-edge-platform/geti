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

import { ExportDatasetStatusDTO } from '../../configurable-parameters/dtos/configurable-parameters.interface';
import { JobExportStatus, JobProjectExportStatus, JobStatusIdentifier } from '../../jobs/jobs.interface';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { DOMAIN, ProjectIdentifier } from '../core.interface';
import {
    CreateDatasetBody,
    CreateDatasetResponse,
    Dataset,
    DatasetIdentifier,
    DeleteDatasetResponse,
    ExportDatasetIdentifier,
    ExportDatasetStatusIdentifier,
} from '../dataset.interface';
import { ProjectStatus } from '../project-status.interface';
import {
    CreateProjectProps,
    EditProjectProps,
    ProjectExport,
    ProjectExportIdentifier,
    ProjectImport,
    ProjectImportIdentifier,
    ProjectImportStatus,
    ProjectName,
    ProjectProps,
} from '../project.interface';
import { TaskMetadata } from '../task.interface';

export interface ImportOptions {
    skipSignatureVerification: boolean;
    keepOriginalDates: boolean;
    projectName: string;
}

export enum ProjectSortingOptions {
    name = 'name',
    creationDate = 'creation_date',
}

export interface ProjectsQueryOptions {
    sortBy: ProjectSortingOptions;
    sortDir: 'asc' | 'dsc';
    name?: string;
}

export interface ProjectService {
    getProjects(
        workspaceIdentifier: WorkspaceIdentifier,
        queryOptions: ProjectsQueryOptions,
        nextPage?: string | null | undefined,
        withSize?: boolean
    ): Promise<{
        projects: ProjectProps[];
        nextPage: NextPageURL;
    }>;
    getProject(projectIdentifier: ProjectIdentifier): Promise<ProjectProps>;
    getProjectNames(workspaceIdentifier?: WorkspaceIdentifier): Promise<{ projects: ProjectName[] }>;
    createDataset({ projectIdentifier, name }: CreateDatasetBody): Promise<CreateDatasetResponse>;
    deleteDataset(datasetIdentifier: DatasetIdentifier): Promise<DeleteDatasetResponse>;
    updateDataset(datasetIdentifier: DatasetIdentifier, updatedDataset: Dataset): Promise<CreateDatasetResponse>;
    editProject(
        projectIdentifier: ProjectIdentifier,
        body: EditProjectProps,
        anomalyRevampFlagEnabled?: boolean
    ): Promise<ProjectProps>;
    createProject(
        workspaceIdentifier: WorkspaceIdentifier,
        name: string,
        domains: DOMAIN[],
        projectTypeMetadata: TaskMetadata[],
        anomalyRevampFlagEnabled?: boolean
    ): Promise<CreateProjectProps>;
    exportProject(projectIdentifier: ProjectIdentifier): Promise<ProjectExport>;
    exportProjectStatus(projectIdentifier: ProjectExportIdentifier): Promise<JobProjectExportStatus>;
    importProject(projectImportFileIdentifier: ProjectImportIdentifier, options: ImportOptions): Promise<ProjectImport>;
    getImportProjectStatus(projectImportIdentifier: ProjectImportIdentifier): Promise<ProjectImportStatus>;
    deleteProject(projectIdentifier: ProjectIdentifier): Promise<string>;
    getProjectStatus(projectIdentifier: ProjectIdentifier): Promise<ProjectStatus>;
    prepareExportDatasetJob(exportDatasetIdentifier: ExportDatasetIdentifier): Promise<{ jobId: string }>;
    exportDatasetStatus(exportDatasetStatusIdentifier: ExportDatasetStatusIdentifier): Promise<ExportDatasetStatusDTO>;
    exportDatasetStatusJob(exportDatasetStatusIdentifier: JobStatusIdentifier): Promise<JobExportStatus>;
}
