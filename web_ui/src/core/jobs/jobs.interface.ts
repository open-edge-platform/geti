// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceIdentifier } from '../../../packages/core/src/workspaces/services/workspaces.interface';
import { DatasetImportSupportedProjectType, DatasetImportWarning } from '../datasets/dataset.interface';
import { Dataset } from '../projects/dataset.interface';
import { JobState, JobStepState, JobType } from './jobs.const';

export interface JobStep {
    message: string | null;
    index: number;
    progress: number | null;
    state: JobStepState;
    stepName: string;
    warning?: string;
    duration?: number;
}

export interface JobCount {
    numberOfRunningJobs: number | null;
    numberOfFinishedJobs: number | null;
    numberOfScheduledJobs: number | null;
    numberOfCancelledJobs: number | null;
    numberOfFailedJobs: number | null;
}

interface JobProjectMetadata {
    project: {
        id: string;
        name: string;
    };
}

interface JobScoreMetadata {
    taskId: string;
    score: number;
}

interface JobOptimizationMetadata {
    modelStorageId: string;
    baseModelId: string;
    optimizationType: string;
    optimizedModelId?: string;
}

interface JobBaseMetadata {
    datasetStorageId: string;
    modelArchitecture?: string;
    modelTemplateId?: string;
    taskId: string;
    name?: string;
    scores?: JobScoreMetadata[];
}

interface JobTestModelMetadata {
    id: string;
    architectureName: string;
    modelTemplateId: string;
    hasExplainableAI: boolean;
    optimizationType: string;
    precision: string[];
}

interface JobTestMetadata extends JobProjectMetadata {
    task: Pick<JobBaseMetadata, 'taskId'>;
    test: {
        datasets: Pick<Dataset, 'name' | 'id'>[];
        model: JobTestModelMetadata;
    };
}

export interface JobCostConsumed {
    unit: string;
    amount: number;
    consumingDate: string;
}

export interface JobCostProps {
    requests: { unit: string; amount: number }[];
    leaseId: string;
    consumed: JobCostConsumed[];
}

export interface JobGeneralProps {
    id: string;
    creationTime: string;
    startTime: string | null;
    endTime: string | null;
    name: string;
    authorId: string;
    state: JobState;
    steps: JobStep[];
    cancellationInfo: {
        isCancelled: boolean;
        userUId: string | null;
        cancelTime: string | null;
        isCancellable: boolean;
    };
    cost?: JobCostProps;
}

export interface JobTest extends JobGeneralProps {
    type: JobType.TEST;
    metadata: JobTestMetadata;
}

export interface JobTask extends JobGeneralProps {
    type: JobType.TRAIN;
    metadata: {
        task: JobBaseMetadata;
        trainedModel: {
            modelId: string | undefined;
        };
    } & JobProjectMetadata;
}

export interface JobOptimization extends JobGeneralProps {
    type: JobType.OPTIMIZATION_POT;
    metadata: {
        task: Pick<JobBaseMetadata, 'taskId' | 'modelArchitecture' | 'modelTemplateId'>;
    } & JobProjectMetadata &
        JobOptimizationMetadata;
}

interface RunningJobBaseProps {
    state: JobState.RUNNING;
}

type RunningTestingJob = RunningJobBaseProps & JobTest;

export type RunningTrainingJob = RunningJobBaseProps & JobTask;

export interface JobStatusIdentifier extends WorkspaceIdentifier {
    jobId: string;
}

export type RunningJobProps = RunningTestingJob | RunningTrainingJob;

export interface JobExportStatus extends JobGeneralProps {
    type: JobType.EXPORT_DATASET;
    metadata: {
        downloadUrl?: string;
        project?: {
            id?: string;
            name?: string;
        };
        size?: number;
    };
}

export interface JobPrepareDatasetImportNewProjectStatus extends JobGeneralProps {
    type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT;
    metadata: {
        warnings?: DatasetImportWarning[];
        supportedProjectTypes?: DatasetImportSupportedProjectType[];
    };
}

export interface JobImportDatasetToNewProjectStatus extends JobGeneralProps {
    type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT;
    metadata: { projectId?: string };
}

export interface JobPrepareDatasetToExistingProjectStatus extends JobGeneralProps {
    type: JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT;
    metadata: {
        labels?: string[];
        warnings?: DatasetImportWarning[];
        project?: {
            id: string;
            name: string;
        };
    };
}

export interface JobImportDatasetToExistingProjectStatus extends JobGeneralProps {
    type: JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT;
    metadata: {
        dataset?: {
            id: string;
            name: string;
            useForTraining: boolean;
            creationTime: string;
        };
        project?: {
            id: string;
            name: string;
        };
    };
}

export type JobDataset =
    | JobExportStatus
    | JobPrepareDatasetImportNewProjectStatus
    | JobImportDatasetToNewProjectStatus
    | JobPrepareDatasetToExistingProjectStatus
    | JobImportDatasetToExistingProjectStatus;

export interface JobProjectExportStatus extends JobGeneralProps {
    type: JobType.EXPORT_PROJECT;
    metadata: {
        includePersonalData?: boolean;
        includeModels?: boolean;
        downloadUrl?: string;
        project: {
            id: string;
            name: string;
        };
    };
}

export interface JobProjectImportStatus extends JobGeneralProps {
    type: JobType.IMPORT_PROJECT;
    metadata: {
        fileId: string;
        keepOriginalDates: boolean;
        skipSignatureVerification: boolean;
        project: {
            id?: string;
            name: string;
        };
    };
}

export type Job = JobTest | JobTask | JobOptimization | JobDataset | JobProjectExportStatus | JobProjectImportStatus;
