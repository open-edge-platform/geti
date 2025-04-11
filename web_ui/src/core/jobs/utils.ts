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

import isNil from 'lodash/isNil';
import overSome from 'lodash/overSome';

import { getSupportedProjectTypesFromDTO, getWarningsFromDTO } from '../datasets/services/utils';
import {
    JobCountDTO,
    JobDatasetDTO,
    JobDTO,
    JobExportStatusDTO,
    JobImportDatasetToExistingProjectStatusDTO,
    JobImportDatasetToNewProjectStatusDTO,
    JobImportExportProjectDTO,
    JobOptimizationDTO,
    JobOptimizationMetadataDTO,
    JobPrepareDatasetImportNewProjectStatusDTO,
    JobPrepareDatasetToExistingProjectStatusDTO,
    JobProjectExportStatusDTO,
    JobProjectImportStatusDTO,
    JobTaskDTO,
    JobTaskMetadataDTO,
    JobTestDTO,
    JobTestMetadataDTO,
} from './dtos/jobs-dto.interface';
import { JobStepState, JobType } from './jobs.const';
import {
    Job,
    JobCostProps,
    JobCount,
    JobDataset,
    JobExportStatus,
    JobGeneralProps,
    JobImportDatasetToExistingProjectStatus,
    JobImportDatasetToNewProjectStatus,
    JobOptimization,
    JobPrepareDatasetImportNewProjectStatus,
    JobPrepareDatasetToExistingProjectStatus,
    JobProjectExportStatus,
    JobProjectImportStatus,
    JobStep,
    JobTask,
    JobTest,
} from './jobs.interface';

const getJobTestMetadata = ({ test, task, project }: JobTestMetadataDTO): Pick<JobTest, 'type' | 'metadata'> => {
    const { model, datasets } = test;
    const { id, architecture, optimization_type, has_xai_head, template_id, precision } = model;

    return {
        type: JobType.TEST,
        metadata: {
            project,
            task: { taskId: task.task_id },
            test: {
                datasets,
                model: {
                    id,
                    precision,
                    architectureName: architecture,
                    modelTemplateId: template_id,
                    hasExplainableAI: has_xai_head,
                    optimizationType: optimization_type,
                },
            },
        },
    };
};

const getJobTaskMetadata = ({
    task,
    project,
    trained_model,
}: JobTaskMetadataDTO): Pick<JobTask, 'type' | 'metadata'> => {
    const { model_architecture, model_template_id, task_id, name, dataset_storage_id, scores } = task;

    return {
        type: JobType.TRAIN,
        metadata: {
            project,
            task: {
                name,
                taskId: task_id,
                modelTemplateId: model_template_id,
                modelArchitecture: model_architecture,
                datasetStorageId: dataset_storage_id,
                scores: scores?.map(({ score, task_id: taskId }) => ({ score, taskId })),
            },
            trainedModel: {
                modelId: trained_model?.model_id,
            },
        },
    };
};

const getJobOptimizationMetadata = (
    {
        task,
        project,
        model_storage_id,
        base_model_id,
        optimized_model_id,
        optimization_type,
    }: JobOptimizationMetadataDTO,
    jobType: JobType.OPTIMIZATION_POT
): Pick<JobOptimization, 'type' | 'metadata'> => {
    const { task_id, model_architecture, model_template_id } = task;

    return {
        type: jobType,
        metadata: {
            project,
            modelStorageId: model_storage_id,
            baseModelId: base_model_id,
            optimizedModelId: optimized_model_id,
            optimizationType: optimization_type,
            task: { taskId: task_id, modelArchitecture: model_architecture, modelTemplateId: model_template_id },
        },
    };
};

const getJobDatasetExportMetadata = (job: JobExportStatusDTO): Pick<JobExportStatus, 'type' | 'metadata'> => {
    return {
        type: JobType.EXPORT_DATASET,
        metadata: {
            downloadUrl: String(job.metadata?.download_url),
            project: {
                id: job.metadata.project?.id,
                name: job.metadata.project?.name,
            },
            size: job.metadata.size,
        },
    };
};

const getJobPrepareDatasetImportNewProjectStatusMetadata = (
    job: JobPrepareDatasetImportNewProjectStatusDTO
): Pick<JobPrepareDatasetImportNewProjectStatus, 'type' | 'metadata'> => {
    return {
        type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT,
        metadata: {
            warnings: getWarningsFromDTO(job.metadata.warnings),
            supportedProjectTypes: getSupportedProjectTypesFromDTO(job.metadata.supported_project_types),
        },
    };
};

const getJobImportDatasetToNewProjectStatusMetadata = (
    job: JobImportDatasetToNewProjectStatusDTO
): Pick<JobImportDatasetToNewProjectStatus, 'type' | 'metadata'> => {
    return {
        type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT,
        metadata: { projectId: job.metadata.project_id },
    };
};

const getJobPrepareDatasetToExistingProjectStatusMetadata = (
    job: JobPrepareDatasetToExistingProjectStatusDTO
): Pick<JobPrepareDatasetToExistingProjectStatus, 'type' | 'metadata'> => {
    return {
        type: JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT,
        metadata: job.metadata,
    };
};

const getJobImportDatasetToExistingProjectStatusMetadata = (
    job: JobImportDatasetToExistingProjectStatusDTO
): Pick<JobImportDatasetToExistingProjectStatus, 'type' | 'metadata'> => {
    return {
        type: JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT,
        metadata: {
            dataset: {
                id: String(job.metadata.dataset?.id),
                name: String(job.metadata.dataset?.name),
                useForTraining: Boolean(job.metadata.dataset?.use_for_training),
                creationTime: String(job.metadata.dataset?.creation_time),
            },
            project: job.metadata.project,
        },
    };
};

const getJobProjectExportMetadata = (
    job: JobProjectExportStatusDTO
): Pick<JobProjectExportStatus, 'type' | 'metadata'> => {
    return {
        type: JobType.EXPORT_PROJECT,
        metadata: {
            downloadUrl: String(job.metadata?.download_url),
            includeModels: job.metadata.include_models,
            includePersonalData: job.metadata.include_personal_data,
            project: {
                id: job.metadata.project.id,
                name: job.metadata.project.name,
            },
        },
    };
};

const getJobProjectImportMetadata = (
    job: JobProjectImportStatusDTO
): Pick<JobProjectImportStatus, 'type' | 'metadata'> => {
    return {
        type: JobType.IMPORT_PROJECT,
        metadata: {
            fileId: job.metadata.parameters.file_id,
            keepOriginalDates: job.metadata.parameters.keep_original_dates,
            skipSignatureVerification: job.metadata.parameters.skip_signature_verification,
            project: {
                id: job.metadata.project?.id,
                name: job.metadata.project?.name ?? '',
            },
        },
    };
};

export const getJobCost = (job: JobDTO): JobCostProps | undefined => {
    if (isNil(job.cost)) {
        return undefined;
    }

    return {
        requests: job.cost.requests,
        leaseId: job.cost.lease_id,
        consumed: job.cost.consumed.map(({ consuming_date, ...info }) => ({ ...info, consumingDate: consuming_date })),
    };
};

export const getJobEntity = (job: JobDTO): Job => {
    let jobMetadata;
    const { end_time, start_time, creation_time, cancellation_info, author, ...others } = job;

    switch (job.type) {
        case JobType.TEST:
            jobMetadata = getJobTestMetadata(job.metadata);
            break;
        case JobType.OPTIMIZATION_POT:
            jobMetadata = getJobOptimizationMetadata(job.metadata, job.type);
            break;
        case JobType.EXPORT_DATASET:
            jobMetadata = getJobDatasetExportMetadata(job);
            break;
        case JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT:
            jobMetadata = getJobPrepareDatasetImportNewProjectStatusMetadata(job);
            break;
        case JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT:
            jobMetadata = getJobImportDatasetToNewProjectStatusMetadata(job);
            break;
        case JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT:
            jobMetadata = getJobPrepareDatasetToExistingProjectStatusMetadata(job);
            break;
        case JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT:
            jobMetadata = getJobImportDatasetToExistingProjectStatusMetadata(job);
            break;
        case JobType.IMPORT_PROJECT:
            jobMetadata = getJobProjectImportMetadata(job);
            break;
        case JobType.EXPORT_PROJECT:
            jobMetadata = getJobProjectExportMetadata(job);
            break;
        default:
            jobMetadata = getJobTaskMetadata(job.metadata);
    }

    return {
        ...others,
        ...jobMetadata,
        cost: getJobCost(job),
        authorId: author,
        endTime: end_time,
        startTime: start_time,
        creationTime: creation_time,
        steps: job.steps.map(({ step_name, ...step }): JobStep => ({ ...step, stepName: step_name })),
        cancellationInfo: {
            isCancelled: cancellation_info.is_cancelled,
            cancelTime: cancellation_info.cancel_time,
            userUId: cancellation_info.user_uid,
            isCancellable: cancellation_info.cancellable,
        },
    };
};

export const getJobActiveStep = (job: JobGeneralProps): JobStep | undefined => {
    const activeStep = job.steps.find((step) => step.state === JobStepState.RUNNING);

    return activeStep ?? job.steps.at(-1);
};

export const isJobTest = <T extends JobTestDTO | JobTest>(job: { type: JobType }): job is T =>
    job.type === JobType.TEST;

export const isJobOptimization = <T extends JobOptimizationDTO | JobOptimization>(job: { type: JobType }): job is T =>
    job.type === JobType.OPTIMIZATION_POT;

export const isJobTrain = <T extends JobTaskDTO | JobTask>(job: { type: JobType }): job is T =>
    job.type === JobType.TRAIN;

export const isJobDatasetExport = <T extends JobExportStatus | JobExportStatusDTO>(job: { type: JobType }): job is T =>
    job.type === JobType.EXPORT_DATASET;

export const isJobProjectExport = <T extends JobProjectExportStatus | JobProjectExportStatusDTO>(job: {
    type: JobType;
}): job is T => job.type === JobType.EXPORT_PROJECT;

export const isJobProjectImport = <T extends JobProjectImportStatus | JobProjectImportStatusDTO>(job: {
    type: JobType;
}): job is T => job.type === JobType.IMPORT_PROJECT;

const isPrepareDatasetIntoNewProjectDTO = (job: { type: JobType }): job is JobPrepareDatasetImportNewProjectStatusDTO =>
    job.type === JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT;

const isImportDatasetIntoNewProjectDTO = (job: { type: JobType }): job is JobImportDatasetToNewProjectStatusDTO =>
    job.type === JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT;

const isPrepareDatasetToExistingProjectDTO = (job: {
    type: JobType;
}): job is JobPrepareDatasetToExistingProjectStatusDTO =>
    job.type === JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT;

const isImportDatasetToExistingProjectDTO = (job: {
    type: JobType;
}): job is JobImportDatasetToExistingProjectStatusDTO =>
    job.type === JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT;

export const isJobDataset = <T extends JobDatasetDTO | JobDataset | JobImportExportProjectDTO>(job: {
    type: JobType;
}): job is T =>
    overSome([
        isJobDatasetExport,
        isJobProjectExport,
        isJobProjectImport,
        isPrepareDatasetIntoNewProjectDTO,
        isImportDatasetIntoNewProjectDTO,
        isPrepareDatasetToExistingProjectDTO,
        isImportDatasetToExistingProjectDTO,
    ])(job);

export const getJobCountEntity = ({
    n_running_jobs,
    n_finished_jobs,
    n_scheduled_jobs,
    n_cancelled_jobs,
    n_failed_jobs,
}: JobCountDTO): JobCount => ({
    numberOfRunningJobs: n_running_jobs,
    numberOfFinishedJobs: n_finished_jobs,
    numberOfScheduledJobs: n_scheduled_jobs,
    numberOfCancelledJobs: n_cancelled_jobs,
    numberOfFailedJobs: n_failed_jobs,
});
