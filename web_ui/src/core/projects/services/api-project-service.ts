// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../../../packages/core/src/services/urls';
import { WorkspaceIdentifier } from '../../../../packages/core/src/workspaces/services/workspaces.interface';
import { isNotCropDomain } from '../../../shared/utils';
import {
    ExportDatasetStatusDTO,
    ExportStatusStateDTO,
} from '../../configurable-parameters/dtos/configurable-parameters.interface';
import {
    JobExportStatusDTO,
    JobProjectExportStatusDTO,
    JobProjectImportStatusDTO,
} from '../../jobs/dtos/jobs-dto.interface';
import { JobState, JobStepState } from '../../jobs/jobs.const';
import { JobExportStatus, JobProjectExportStatus, JobStatusIdentifier } from '../../jobs/jobs.interface';
import { getJobActiveStep, getJobEntity } from '../../jobs/utils';
import { DOMAIN, ProjectIdentifier } from '../core.interface';
import {
    CreateDatasetBody,
    CreateDatasetResponse,
    CreateDatasetResponseDTO,
    Dataset,
    DatasetIdentifier,
    DeleteDatasetResponse,
    ExportDatasetIdentifier,
    ExportDatasetStatusIdentifier,
} from '../dataset.interface';
import { isKeypointDetection } from '../domains';
import { ProjectDTO } from '../dtos/project.interface';
import { ProjectStatusDTO } from '../dtos/status.interface';
import { ProjectExportDTO, ProjectImportDTO } from '../dtos/task.interface';
import { ProjectStatus } from '../project-status.interface';
import {
    CreateProjectProps,
    ProjectExport,
    ProjectExportIdentifier,
    ProjectImport,
    ProjectImportIdentifier,
    ProjectImportStatus,
    ProjectName,
    ProjectProps,
} from '../project.interface';
import { TaskMetadata } from '../task.interface';
import { getFormattedTimeRemaining, getRoundedProgress } from '../utils';
import { ImportOptions, ProjectService, ProjectsQueryOptions } from './project-service.interface';
import {
    getConnectionsByTaskNames,
    getDatasetEntity,
    getEditProjectDTO,
    getPerformance,
    getPreparedKeypointTasks,
    getPreparedTasks,
    getProjectEntity,
} from './utils';

export const JobStateToExportStatus: Record<JobState, ExportStatusStateDTO> = {
    [JobState.CANCELLED]: ExportStatusStateDTO.DONE,
    [JobState.FAILED]: ExportStatusStateDTO.ERROR,
    [JobState.FINISHED]: ExportStatusStateDTO.DONE,
    [JobState.RUNNING]: ExportStatusStateDTO.EXPORTING,
    [JobState.SCHEDULED]: ExportStatusStateDTO.ZIPPING,
};

export const createApiProjectService: CreateApiService<ProjectService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getProjects: ProjectService['getProjects'] = async (
        workspaceIdentifier: WorkspaceIdentifier,
        sortingOptions: ProjectsQueryOptions,
        nextPageUrl: string | null | undefined,
        withSize = false
    ): Promise<{
        projects: ProjectProps[];
        nextPage: string | null | undefined;
    }> => {
        if (!workspaceIdentifier) return { projects: [], nextPage: undefined };

        const url = nextPageUrl ?? router.PROJECTS_SEARCH(workspaceIdentifier, sortingOptions, withSize);

        const response = await instance.get<{
            projects: ProjectDTO[];
            next_page: string;
            project_counts: number;
            project_page_count: number;
        }>(url);

        const projects: ProjectProps[] = (response.data.projects ?? [])
            .map((project) => getProjectEntity(project, router))
            .filter(Boolean);

        const emptyNextPage: boolean = response.data.project_counts === response.data.project_page_count;
        const nextPage: string | null | undefined = emptyNextPage ? undefined : response.data.next_page;

        return { projects, nextPage };
    };

    const getProject = async (projectIdentifier: ProjectIdentifier): Promise<ProjectProps> => {
        const { data } = await instance.get<ProjectDTO>(router.PROJECT(projectIdentifier));

        return getProjectEntity(data, router);
    };

    const getProjectNames = async (workspaceIdentifier: WorkspaceIdentifier): Promise<{ projects: ProjectName[] }> => {
        const { data } = await instance.get<{ projects: ProjectName[] }>(router.PROJECT_NAMES(workspaceIdentifier));
        return data;
    };

    const editProject = async (
        projectIdentifier: ProjectIdentifier,
        project: ProjectProps,
        anomalyRevampFlagEnabled = false
    ): Promise<ProjectProps> => {
        const { data: currentProjectData } = await instance.get<ProjectDTO>(router.PROJECT(projectIdentifier));

        const { data } = await instance.put(
            router.PROJECT(projectIdentifier),
            getEditProjectDTO(project, currentProjectData.pipeline.tasks, anomalyRevampFlagEnabled)
        );

        return getProjectEntity(data, router);
    };

    const importProject = async (
        projectIdentifier: ProjectImportIdentifier,
        options: ImportOptions
    ): Promise<ProjectImport> => {
        const { importProjectId, ...workspaceIdentifier } = projectIdentifier;

        const { data } = await instance.post<ProjectImportDTO>(
            router.PROJECT_IMPORT.IMPORT_PROJECT(workspaceIdentifier),
            {
                file_id: importProjectId,
                project_name: options.projectName,
            }
        );

        return {
            importProjectId: data.job_id,
        };
    };

    const getImportProjectStatus = async ({
        importProjectId,
        ...workspaceIdentifier
    }: ProjectImportIdentifier): Promise<ProjectImportStatus> => {
        const { data: jobData } = await instance.get<JobProjectImportStatusDTO>(
            router.JOB(workspaceIdentifier, importProjectId)
        );
        const job = getJobEntity(jobData);

        const projectId = jobData.metadata.project?.id ?? null;

        const errorMessage = job.steps?.find((step) => step.state === JobStepState.FAILED)?.message ?? null;

        return {
            projectId,
            state: JobStateToExportStatus[job.state],
            progress: getJobActiveStep(job)?.progress ?? 0,
            message: errorMessage,
        };
    };

    const exportProject = async (projectIdentifier: ProjectIdentifier): Promise<ProjectExport> => {
        const { data } = await instance.post<ProjectExportDTO>(router.EXPORT_PROJECT(projectIdentifier));

        return {
            exportProjectId: data.job_id,
        };
    };

    const exportProjectStatus = async ({
        exportProjectId,
        ...projectIdentifier
    }: ProjectExportIdentifier): Promise<JobProjectExportStatus> => {
        const { data: jobData } = await instance.get<JobProjectExportStatusDTO>(
            router.JOB(projectIdentifier, exportProjectId)
        );
        const job = getJobEntity(jobData);

        return job as JobProjectExportStatus;
    };

    const createProject = async (
        workspaceIdentifier: WorkspaceIdentifier,
        name: string,
        domains: DOMAIN[],
        taskMetadata: TaskMetadata[],
        anomalyRevampFlagEnabled = false
    ): Promise<CreateProjectProps> => {
        const filteredDomains = domains.filter(isNotCropDomain);
        const connections = getConnectionsByTaskNames(filteredDomains);

        const tasks = domains.some(isKeypointDetection)
            ? getPreparedKeypointTasks(taskMetadata, filteredDomains)
            : getPreparedTasks(taskMetadata, filteredDomains, anomalyRevampFlagEnabled);

        const body = { name, pipeline: { connections, tasks } };
        const { data } = await instance.post<ProjectDTO>(router.PROJECTS(workspaceIdentifier), body);

        return getProjectEntity(data, router);
    };

    const deleteProject = async (projectIdentifier: ProjectIdentifier): Promise<string> => {
        const { data } = await instance.delete<{ result: string }>(router.PROJECT(projectIdentifier));

        return data.result;
    };

    const getProjectStatus = async (projectIdentifier: ProjectIdentifier): Promise<ProjectStatus> => {
        const url = router.PROJECT_STATUS(projectIdentifier);
        const { data } = await instance.get<ProjectStatusDTO>(url);

        const performance = getPerformance(data.project_performance);

        return {
            performance,
            isTraining: data.is_training,
            trainingDetails: {
                progress: getRoundedProgress(data.status.progress),
                timeRemaining: getFormattedTimeRemaining(data.status.time_remaining),
            },
            tasks: data.tasks,
        };
    };

    const createDataset = async ({ projectIdentifier, name }: CreateDatasetBody): Promise<CreateDatasetResponse> => {
        const { data } = await instance.post<CreateDatasetResponseDTO>(
            router.DATASET.CREATE_DATASET(projectIdentifier),
            { name }
        );

        return getDatasetEntity(data);
    };

    const deleteDataset = async (datasetIdentifier: DatasetIdentifier): Promise<DeleteDatasetResponse> => {
        const { data } = await instance.delete(router.DATASET.DELETE_DATASET(datasetIdentifier));

        return data.result;
    };

    const updateDataset = async (
        datasetIdentifier: DatasetIdentifier,
        updatedDataset: Dataset
    ): Promise<CreateDatasetResponse> => {
        const { id, creationTime, useForTraining, name } = updatedDataset;
        const { data } = await instance.put<CreateDatasetResponseDTO>(
            router.DATASET.UPDATE_DATASET(datasetIdentifier),
            {
                id,
                creation_time: creationTime,
                use_for_training: useForTraining,
                name,
            }
        );

        return getDatasetEntity(data);
    };

    const prepareExportDatasetJob = async ({
        exportFormat,
        saveVideoAsImages,
        ...datasetIdentifier
    }: ExportDatasetIdentifier) => {
        const { data } = await instance.post<{
            job_id: string;
        }>(router.DATASET.PREPARE_EXPORT(datasetIdentifier, exportFormat, saveVideoAsImages));
        return {
            jobId: data.job_id,
        };
    };

    const exportDatasetStatus = async ({
        exportDatasetId,
        ...datasetIdentifier
    }: ExportDatasetStatusIdentifier): Promise<ExportDatasetStatusDTO> => {
        const { data } = await instance.get<ExportDatasetStatusDTO>(
            router.DATASET.EXPORT_STATUS(datasetIdentifier, exportDatasetId)
        );

        return data;
    };

    const exportDatasetStatusJob = async ({
        jobId,
        ...workspaceIdentifier
    }: JobStatusIdentifier): Promise<JobExportStatus> => {
        const { data } = await instance.get<JobExportStatusDTO>(router.JOB(workspaceIdentifier, jobId));

        return getJobEntity(data) as JobExportStatus;
    };

    return {
        getProjects,
        getProject,
        getProjectNames,
        editProject,
        createDataset,
        deleteDataset,
        updateDataset,
        createProject,
        deleteProject,
        getProjectStatus,
        prepareExportDatasetJob,
        exportDatasetStatus,
        exportDatasetStatusJob,
        exportProject,
        exportProjectStatus,
        importProject,
        getImportProjectStatus,
    };
};
