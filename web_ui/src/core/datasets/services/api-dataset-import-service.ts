// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import {
    JobImportDatasetToExistingProjectStatusDTO,
    JobImportDatasetToNewProjectStatusDTO,
    JobPrepareDatasetImportNewProjectStatusDTO,
    JobPrepareDatasetToExistingProjectStatusDTO,
} from '../../jobs/dtos/jobs-dto.interface';
import {
    JobImportDatasetToExistingProjectStatus,
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
    JobPrepareDatasetToExistingProjectStatus,
    JobStatusIdentifier,
} from '../../jobs/jobs.interface';
import { getJobEntity } from '../../jobs/utils';
import { CreateDatasetResponse } from '../../projects/dataset.interface';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
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
import {
    DatasetImportPrepareForNewProjectResponseDTO,
    DatasetImportToExistingProjectResponseDTO,
    DatasetImportToNewProjectPayloadDTO,
    DatasetImportToNewProjectResponseDTO,
    DatasetImportWarningDTO,
    DatasetPrepareForExistingProjectResponseDTO,
} from '../dtos/dataset.interface';
import { DatasetImportService } from './dataset.interface';
import { getSupportedProjectTypesFromDTO, getTaskTypeDTOFromTaskType, getWarningsFromDTO } from './utils';

/*
    This service is used to create a new project based on an imported dataset
    or to add a dataset to an existing project
*/
export const createApiDatasetImportService: CreateApiService<DatasetImportService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const prepareDatasetForNewProject = async ({
        uploadId,
        setAbortController,
        ...workspaceIdentifier
    }: DatasetImportIdentifier): Promise<DatasetImportPrepareForNewProjectResponse> => {
        const abortController: AbortController = new AbortController();
        setAbortController(uploadId, abortController);

        const { data } = await instance.post<DatasetImportPrepareForNewProjectResponseDTO>(
            `${router.DATASET.IMPORT_PREPARE(workspaceIdentifier, uploadId)}`,
            null,
            { signal: abortController.signal }
        );

        return {
            warnings: getWarningsFromDTO(data.warnings),
            supportedProjectTypes: getSupportedProjectTypesFromDTO(data.supported_project_types),
        };
    };

    const prepareDatasetJob = async ({
        uploadId,
        setAbortController,
        ...workspaceIdentifier
    }: DatasetImportIdentifier) => {
        const abortController: AbortController = new AbortController();
        setAbortController(uploadId, abortController);

        const { data } = await instance.post<{ job_id: string }>(
            `${router.DATASET.IMPORT_PREPARE(workspaceIdentifier, uploadId)}`,
            null,
            { signal: abortController.signal }
        );

        return {
            jobId: data.job_id,
        };
    };

    const prepareDatasetImportNewProjectJob = async ({
        jobId,
        ...workspaceIdentifier
    }: JobStatusIdentifier): Promise<JobPrepareDatasetImportNewProjectStatus> => {
        const { data } = await instance.get<JobPrepareDatasetImportNewProjectStatusDTO>(
            router.JOB(workspaceIdentifier, jobId)
        );

        return getJobEntity(data) as JobPrepareDatasetImportNewProjectStatus;
    };

    const importDatasetToNewProjectStatusJob = async ({
        jobId,
        ...workspaceIdentifier
    }: JobStatusIdentifier): Promise<JobImportDatasetToNewProjectStatus> => {
        const { data } = await instance.get<JobImportDatasetToNewProjectStatusDTO>(
            router.JOB(workspaceIdentifier, jobId)
        );

        return getJobEntity(data) as JobImportDatasetToNewProjectStatus;
    };

    const importDatasetToNewProject = async ({
        projectData,
        setAbortController,
        anomalyRevamp,
        ...workspaceIdentifier
    }: DatasetImportToNewProjectIdentifier): Promise<DatasetImportToNewProjectResponse> => {
        const { uploadId, projectName, taskType, labels } = projectData;

        const projectDataDto: DatasetImportToNewProjectPayloadDTO = {
            file_id: uploadId,
            project_name: projectName,
            task_type: getTaskTypeDTOFromTaskType(taskType, anomalyRevamp),
            labels,
        };

        const abortController = new AbortController();
        setAbortController(uploadId, abortController);

        const { data } = await instance.post<DatasetImportToNewProjectResponseDTO>(
            `${router.DATASET.IMPORT_CREATE(workspaceIdentifier)}`,
            projectDataDto,
            { signal: abortController.signal }
        );

        return { projectId: data.project_id };
    };

    const importDatasetToNewProjectJob = async ({
        projectData,
        setAbortController,
        anomalyRevamp,
        ...workspaceIdentifier
    }: DatasetImportToNewProjectIdentifier): Promise<{ jobId: string }> => {
        const abortController = new AbortController();
        setAbortController(projectData.uploadId, abortController);

        const { data } = await instance.post<{ job_id: string }>(
            `${router.DATASET.IMPORT_CREATE(workspaceIdentifier)}`,
            {
                file_id: projectData.uploadId,
                project_name: projectData.projectName,
                task_type: getTaskTypeDTOFromTaskType(projectData.taskType, anomalyRevamp),
                labels: projectData.labels,
            },
            { signal: abortController.signal }
        );

        return {
            jobId: data.job_id,
        };
    };

    const prepareDatasetToExistingProject = async ({
        uploadId,
        setAbortController,
        ...projectIdentifier
    }: DatasetPrepareForExistingProjectIdentifier): Promise<DatasetPrepareForExistingProjectResponse> => {
        const abortController = new AbortController();
        setAbortController(uploadId, abortController);

        const { data } = await instance.post<DatasetPrepareForExistingProjectResponseDTO>(
            router.DATASET.IMPORT_TO_EXISTING_PROJECT_PREPARE(projectIdentifier, uploadId),
            null,
            { signal: abortController.signal }
        );

        return {
            labels: data.labels,
            warnings: data.warnings.map((warningDTO: DatasetImportWarningDTO) => ({
                type: warningDTO.type,
                name: warningDTO.name,
                description: warningDTO.description,
                affectedImages: warningDTO.affected_images,
                resolveStrategy: warningDTO.resolve_strategy,
            })),
        };
    };

    const prepareDatasetToExistingProjectJob = async ({
        uploadId,
        setAbortController,
        ...projectIdentifier
    }: DatasetPrepareForExistingProjectIdentifier) => {
        const abortController = new AbortController();
        setAbortController(uploadId, abortController);

        const { data } = await instance.post<{ job_id: string }>(
            router.DATASET.IMPORT_TO_EXISTING_PROJECT_PREPARE(projectIdentifier, uploadId),
            null,
            { signal: abortController.signal }
        );

        return {
            jobId: data.job_id,
        };
    };

    const prepareDatasetToExistingProjectStatusJob = async ({
        jobId,
        ...workspaceIdentifier
    }: JobStatusIdentifier): Promise<JobPrepareDatasetToExistingProjectStatus> => {
        const { data } = await instance.get<JobPrepareDatasetToExistingProjectStatusDTO>(
            router.JOB(workspaceIdentifier, jobId)
        );

        return getJobEntity(data) as JobPrepareDatasetToExistingProjectStatus;
    };

    const importDatasetToExistingProject = async ({
        uploadId,
        datasetId,
        datasetName,
        labelsMap,
        setAbortController,
        ...projectIdentifier
    }: DatasetImportToExistingProjectIdentifier): Promise<CreateDatasetResponse> => {
        const abortController = new AbortController();
        setAbortController(uploadId, abortController);

        const { data } = await instance.post<DatasetImportToExistingProjectResponseDTO>(
            router.DATASET.IMPORT_TO_EXISTING_PROJECT(projectIdentifier),
            {
                file_id: uploadId,
                dataset_id: datasetId,
                dataset_name: datasetName,
                labels_map: labelsMap,
            },
            { signal: abortController.signal }
        );

        const { dataset } = data;
        const { id, name, creation_time, use_for_training } = dataset;

        return {
            id,
            name,
            creationTime: creation_time,
            useForTraining: use_for_training,
        };
    };

    const importDatasetToExistingProjectJob = async ({
        uploadId,
        datasetId,
        datasetName,
        labelsMap,
        setAbortController,
        ...projectIdentifier
    }: DatasetImportToExistingProjectIdentifier): Promise<{ jobId: string }> => {
        const abortController = new AbortController();
        setAbortController(uploadId, abortController);

        const { data } = await instance.post<{ job_id: string }>(
            router.DATASET.IMPORT_TO_EXISTING_PROJECT(projectIdentifier),
            {
                file_id: uploadId,
                dataset_id: datasetId,
                dataset_name: datasetName,
                labels_map: labelsMap,
            },
            { signal: abortController.signal }
        );

        return {
            jobId: data.job_id,
        };
    };

    const importDatasetToExistingProjectStatusJob = async ({
        jobId,
        ...workspaceIdentifier
    }: JobStatusIdentifier): Promise<JobImportDatasetToExistingProjectStatus> => {
        const { data } = await instance.get<JobImportDatasetToExistingProjectStatusDTO>(
            router.JOB(workspaceIdentifier, jobId)
        );

        return getJobEntity(data) as JobImportDatasetToExistingProjectStatus;
    };

    const deleteImportProjectFromDataset = async (
        workspaceIdentifier: WorkspaceIdentifier & { fileId: string }
    ): Promise<void> => {
        const response = await instance.delete<void>(router.DATASET.IMPORT_TUS_FILE(workspaceIdentifier));

        return response.data;
    };

    return {
        prepareDatasetJob,

        prepareDatasetForNewProject,
        prepareDatasetImportNewProjectJob,

        importDatasetToNewProject,
        importDatasetToNewProjectJob,
        importDatasetToNewProjectStatusJob,

        prepareDatasetToExistingProject,
        prepareDatasetToExistingProjectJob,
        prepareDatasetToExistingProjectStatusJob,

        importDatasetToExistingProject,
        importDatasetToExistingProjectJob,
        importDatasetToExistingProjectStatusJob,

        deleteImportProjectFromDataset,
    };
};
