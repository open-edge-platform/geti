// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DatasetImportSupportedProjectTypeDTO, DatasetImportWarningDTO } from '../../datasets/dtos/dataset.interface';
import { DatasetDTO } from '../../projects/dtos/project.interface';
import { JobState, JobStepState, JobType } from '../jobs.const';

export interface JobsResponseDTO {
    jobs: JobDTO[];
    jobs_count: JobCountDTO;
    next_page: string | undefined;
}

export interface JobStepDTO {
    message: string | null;
    index: number;
    progress: number | null;
    state: JobStepState;
    step_name: string;
}

export interface JobCountDTO {
    n_running_jobs: number;
    n_finished_jobs: number;
    n_scheduled_jobs: number;
    n_cancelled_jobs: number;
    n_failed_jobs: number;
}

interface JobProjectMetadataDTO {
    project: {
        id: string;
        name: string;
    };
}

interface JobScoreMetadataDTO {
    task_id: string;
    score: number;
}

interface JobOptimizationBaseMetadataDTO {
    model_storage_id: string;
    base_model_id: string;
    optimization_type: string;
    optimized_model_id?: string;
}

interface JobBaseMetadataDTO {
    dataset_storage_id: string;
    model_architecture?: string;
    model_template_id?: string;
    task_id: string;
    name?: string;
    scores?: JobScoreMetadataDTO[];
}

interface JobTestModelMetadataDTO {
    id: string;
    architecture: string;
    template_id: string;
    has_xai_head: boolean;
    optimization_type: string;
    precision: string[];
}
interface JobTrainedModelMetadataDTO {
    model_id: string;
}

export interface JobTaskMetadataDTO extends JobProjectMetadataDTO {
    task: JobBaseMetadataDTO;
    trained_model: JobTrainedModelMetadataDTO | undefined;
}

export interface JobOptimizationMetadataDTO extends JobProjectMetadataDTO, JobOptimizationBaseMetadataDTO {
    task: Pick<JobBaseMetadataDTO, 'task_id' | 'model_architecture' | 'model_template_id'>;
}

export interface JobTestMetadataDTO extends JobProjectMetadataDTO {
    task: Pick<JobBaseMetadataDTO, 'task_id'>;
    test: {
        datasets: Pick<DatasetDTO, 'name' | 'id'>[];
        model: JobTestModelMetadataDTO;
    };
}

export interface JobCostPropsDTO {
    requests: { unit: string; amount: number }[];
    lease_id: string;
    consumed: { unit: string; amount: number; consuming_date: string }[];
}

export interface JobGeneralPropsDTO {
    id: string;
    creation_time: string;
    start_time: string | null;
    end_time: string | null;
    name: string;
    author: string;
    state: JobState;
    steps: JobStepDTO[];
    cancellation_info: {
        is_cancelled: boolean;
        user_uid: string | null;
        cancel_time: string | null;
        cancellable: boolean;
    };
    cost?: JobCostPropsDTO;
}

export interface JobTestDTO extends JobGeneralPropsDTO {
    type: JobType.TEST;
    metadata: JobTestMetadataDTO;
}

export interface JobTaskDTO extends JobGeneralPropsDTO {
    type: JobType.TRAIN;
    metadata: { task: JobBaseMetadataDTO; trained_model: JobTrainedModelMetadataDTO } & JobProjectMetadataDTO;
}

export interface JobOptimizationDTO extends JobGeneralPropsDTO {
    type: JobType.OPTIMIZATION_POT;
    metadata: {
        task: Pick<JobBaseMetadataDTO, 'task_id' | 'model_architecture' | 'model_template_id'>;
    } & JobProjectMetadataDTO &
        JobOptimizationBaseMetadataDTO;
}

export interface JobExportStatusDTO extends JobGeneralPropsDTO {
    type: JobType.EXPORT_DATASET;
    metadata: {
        download_url?: string;
        project?: {
            id?: string;
            name?: string;
        };
        size?: number;
    };
}
export interface JobPrepareDatasetImportNewProjectStatusDTO extends JobGeneralPropsDTO {
    type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT;
    metadata: {
        warnings?: DatasetImportWarningDTO[];
        supported_project_types?: DatasetImportSupportedProjectTypeDTO[];
    };
}

export interface JobImportDatasetToNewProjectStatusDTO extends JobGeneralPropsDTO {
    type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT;
    metadata: { project_id?: string };
}

export interface JobPrepareDatasetToExistingProjectStatusDTO extends JobGeneralPropsDTO {
    type: JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT;
    metadata: {
        labels?: string[];
        warnings?: DatasetImportWarningDTO[];
        project?: {
            id: string;
            name: string;
        };
    };
}

export interface JobImportDatasetToExistingProjectStatusDTO extends JobGeneralPropsDTO {
    type: JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT;
    metadata: {
        dataset?: {
            id: string;
            name: string;
            use_for_training: boolean;
            creation_time: string;
        };
        project?: {
            id: string;
            name: string;
        };
    };
}

export type JobDatasetDTO =
    | JobExportStatusDTO
    | JobPrepareDatasetImportNewProjectStatusDTO
    | JobImportDatasetToNewProjectStatusDTO
    | JobPrepareDatasetToExistingProjectStatusDTO
    | JobImportDatasetToExistingProjectStatusDTO;

export interface JobProjectImportStatusDTO extends JobGeneralPropsDTO {
    type: JobType.IMPORT_PROJECT;
    metadata: {
        parameters: {
            file_id: string;
            skip_signature_verification: boolean;
            keep_original_dates: boolean;
        };
        project?: {
            id: string;
            name: string;
        };
    };
}

export interface JobProjectExportStatusDTO extends JobGeneralPropsDTO {
    type: JobType.EXPORT_PROJECT;
    metadata: {
        project: {
            id: string;
            name: string;
        };
        include_personal_data: boolean;
        include_models: boolean;
        download_url?: string;
    };
}

export type JobImportExportProjectDTO = JobProjectExportStatusDTO | JobProjectImportStatusDTO;

export type JobDTO = JobTestDTO | JobTaskDTO | JobOptimizationDTO | JobDatasetDTO | JobImportExportProjectDTO;
