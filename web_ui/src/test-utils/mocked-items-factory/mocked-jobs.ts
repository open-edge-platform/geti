// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    DATASET_IMPORT_STATUSES,
    DATASET_IMPORT_TASK_TYPE,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
} from '../../core/datasets/dataset.enum';
import { DatasetImportToNewProjectItem } from '../../core/datasets/dataset.interface';
import { JobGeneralPropsDTO } from '../../core/jobs/dtos/jobs-dto.interface';
import { JobState, JobStepState, JobType } from '../../core/jobs/jobs.const';
import {
    Job,
    JobCount,
    JobExportStatus,
    JobImportDatasetToExistingProjectStatus,
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
    JobPrepareDatasetToExistingProjectStatus,
    JobProjectExportStatus,
    JobStep,
    RunningTrainingJob,
} from '../../core/jobs/jobs.interface';

export const getMockedJobStep = (step: Partial<JobStep>) => ({
    index: 1,
    message: 'This is running test step',
    progress: 98,
    state: JobStepState.RUNNING,
    stepName: 'Test step',
    ...step,
});

export const getMockedJob = (job: Partial<Job> = {}): Job => {
    return {
        id: 'job-1',
        name: 'Train task job',
        state: JobState.RUNNING,
        metadata: {
            task: {
                modelArchitecture: 'YoloV4',
                name: 'Detection',
                datasetStorageId: 'dataset-storage-id',
                modelTemplateId: 'template-id',
                taskId: 'detection-task-id',
                scores: [{ score: 98, taskId: 'detection-task-id' }],
            },
            project: {
                id: '123',
                name: 'example project',
            },
            trainedModel: {
                modelId: 'model-id',
            },
        },
        type: JobType.TRAIN,
        startTime: '20/03/2022',
        authorId: 'admin@intel.com',
        creationTime: '20/03/2022',
        endTime: null,
        steps: [
            {
                index: 1,
                message: 'This is running test step',
                progress: 98,
                state: JobStepState.RUNNING,
                stepName: 'Test step',
            },
        ],
        cancellationInfo: {
            isCancelled: false,
            userUId: 'user_uid',
            cancelTime: 'cancel_time',
            isCancellable: true,
        },
        ...job,
    } as Job;
};

export const getMockedGeneralJobDTO = (job: Partial<JobGeneralPropsDTO> = {}): JobGeneralPropsDTO => {
    return {
        id: 'job-1',
        name: 'Train task job',
        state: JobState.RUNNING,
        start_time: '20/03/2022',
        author: 'admin@intel.com',
        creation_time: '20/03/2022',
        end_time: null,
        steps: [
            {
                message: 'This is running test step',
                index: 1,
                progress: 98,
                state: JobStepState.RUNNING,
                step_name: 'Test step',
            },
        ],
        cancellation_info: {
            is_cancelled: false,
            user_uid: 'user_uid',
            cancel_time: 'cancel_time',
            cancellable: false,
        },
        ...job,
    };
};

const runningStep: JobStep = {
    index: 1,
    message: 'This is running test step',
    progress: 98,
    state: JobStepState.RUNNING,
    stepName: 'Test step',
};

export const mockedJobs: Job[] = [
    {
        id: 'job-1',
        name: 'Train task job',
        state: JobState.RUNNING,
        metadata: {
            task: {
                modelArchitecture: 'YoloV4',
                name: 'Detection',
                datasetStorageId: 'dataset-storage-id',
                modelTemplateId: 'template-id',
                taskId: 'detection-task-id',
                scores: [{ score: 98, taskId: 'detection-task-id' }],
            },
            project: {
                id: '123',
                name: 'example project',
            },
            trainedModel: {
                modelId: 'model-id',
            },
        },
        type: JobType.TRAIN,
        startTime: '20/03/2022',
        authorId: 'admin@intel.com',
        creationTime: '20/03/2022',
        endTime: null,
        steps: [runningStep],
        cancellationInfo: {
            isCancelled: false,
            userUId: null,
            cancelTime: null,
            isCancellable: true,
        },
    },
    {
        id: 'job-2',
        name: 'Train task job',
        state: JobState.RUNNING,
        metadata: {
            task: {
                modelArchitecture: 'YoloV4',
                name: 'Detection',
                datasetStorageId: 'dataset-storage-id',
                modelTemplateId: 'template-id',
                taskId: 'detection-task-id',
                scores: [{ score: 98, taskId: 'detection-task-id' }],
            },
            project: {
                id: '123',
                name: 'example project',
            },
            trainedModel: {
                modelId: 'model-id',
            },
        },
        type: JobType.TRAIN,
        startTime: '20/03/2022',
        authorId: 'admin@intel.com',
        creationTime: '20/03/2022',
        endTime: null,
        steps: [runningStep],
        cancellationInfo: {
            isCancelled: false,
            userUId: null,
            cancelTime: null,
            isCancellable: true,
        },
    },
    {
        id: '60ed89589e7651b7da5654ec',
        name: 'Train task job',
        state: JobState.FAILED,
        metadata: {
            task: {
                taskId: 'detection-task-id',
                modelArchitecture: 'YoloV4',
                name: 'Detection',
                datasetStorageId: 'dataset-storage-id',
                modelTemplateId: 'template-id',
            },
            project: {
                id: '1235',
                name: 'example project 3',
            },
            trainedModel: {
                modelId: 'model-id',
            },
        },
        type: JobType.TRAIN,
        startTime: '20/03/2022',
        authorId: 'admin@intel.com',
        creationTime: '20/03/2022',
        endTime: null,
        steps: [runningStep],
        cancellationInfo: {
            isCancelled: false,
            userUId: null,
            cancelTime: null,
            isCancellable: true,
        },
    },
];

export const getMockedProjectExportJob = (job: Partial<JobProjectExportStatus> = {}): JobProjectExportStatus => {
    return {
        id: '670e2278e34f232629cc5d0f',
        type: JobType.EXPORT_PROJECT,
        name: 'Project Export',
        state: JobState.FINISHED,
        steps: [
            {
                message: 'Project export complete',
                index: 1,
                progress: 100,
                state: JobStepState.FINISHED,
                duration: 62.033,
                stepName: 'Exporting project',
            },
        ],
        metadata: {
            downloadUrl:
                // eslint-disable-next-line max-len
                'api/v1/organizations/2e0d93df-5ba5-4a83-bfcc-1db631e3eb49/workspaces/416de51f-c19b-4f52-b9c9-b6b0f912dfaf/projects/4f7f233b8d4868886054fa7e/exports/670e22b2506faff2b1b12242/download',
            project: {
                id: '4f7f233b8d4868886054fa7e',
                name: 'Fish detection classification',
            },
        },
        authorId: '625d92df-9148-46a8-b588-0ecf358379a3',
        endTime: '2024-10-15T08:07:31.820000+00:00',
        startTime: '2024-10-15T08:06:22.785000+00:00',
        creationTime: '2024-10-15T08:06:16.089000+00:00',
        cancellationInfo: {
            isCancelled: false,
            cancelTime: null,
            userUId: null,
            isCancellable: true,
        },
        ...job,
    };
};

export const getMockedDatasetExportJob = (job: Partial<JobExportStatus>): JobExportStatus => {
    return {
        id: '6513c1c81b63044e0b08afe5',
        type: JobType.EXPORT_DATASET,
        creationTime: '2023-09-27T05:46:48.655000+00:00',
        startTime: null,
        endTime: null,
        name: 'prepare import new project job',
        authorId: 'admin@intel.com',
        state: JobState.SCHEDULED,
        steps: [],
        cancellationInfo: {
            isCancelled: false,
            userUId: null,
            cancelTime: null,
            isCancellable: true,
        },
        metadata: { downloadUrl: 'downloadUrl-test', project: { id: 'some-id', name: 'some-name' } },
        ...job,
    };
};

export const getMockedPrepareJob = (
    job: Partial<JobPrepareDatasetImportNewProjectStatus>
): JobPrepareDatasetImportNewProjectStatus | JobPrepareDatasetToExistingProjectStatus => {
    return {
        id: '6513c1c81b63044e0b08afe5',
        type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT,
        creationTime: '2023-09-27T05:46:48.655000+00:00',
        startTime: null,
        endTime: null,
        name: 'prepare import new project job',
        authorId: 'admin@intel.com',
        state: JobState.SCHEDULED,
        steps: [],
        cancellationInfo: {
            isCancelled: false,
            userUId: null,
            cancelTime: null,
            isCancellable: true,
        },
        metadata: {},
        ...job,
    };
};

export const getMockedImportStatusJob = (
    job: Partial<JobImportDatasetToNewProjectStatus>
): JobImportDatasetToNewProjectStatus | JobImportDatasetToExistingProjectStatus => {
    return {
        id: '6513c1c81b63044e0b08afe5',
        type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT,
        creationTime: '2023-09-27T05:46:48.655000+00:00',
        startTime: null,
        endTime: null,
        name: 'Create and Import to New Project',
        authorId: 'admin@intel.com',
        state: JobState.SCHEDULED,
        steps: [],
        cancellationInfo: {
            isCancelled: false,
            userUId: null,
            cancelTime: null,
            isCancellable: true,
        },
        metadata: {},
        ...job,
    };
};

export const mockedRunningTrainingJobs: RunningTrainingJob[] = mockedJobs.filter(
    ({ state, type }) => type === JobType.TRAIN && state === JobState.RUNNING
) as RunningTrainingJob[];

export const getMockedDatasetImportItem = (
    data: Partial<DatasetImportToNewProjectItem>
): DatasetImportToNewProjectItem => ({
    id: '987-654-321',
    name: 'Test Dataset',
    size: '1Gb',
    preparingJobId: null,
    status: DATASET_IMPORT_STATUSES.UPLOADING,
    progress: 50,
    startAt: 0,
    startFromBytes: 0,
    uploadId: '192-837-465',
    bytesRemaining: '500Mb',
    timeRemaining: '10 minutes',
    projectName: '',
    taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
    warnings: [],
    labels: [],
    firstChainTaskType: null,
    firstChainLabels: [],
    labelsToSelect: [],
    labelColorMap: {},
    supportedProjectTypes: [],
    activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
    openedSteps: [],
    completedSteps: [],
    ...data,
});

export const getMockedJobCount = (jobCount?: Partial<JobCount>) => ({
    numberOfRunningJobs: 0,
    numberOfFinishedJobs: 0,
    numberOfScheduledJobs: 0,
    numberOfCancelledJobs: 0,
    numberOfFailedJobs: 0,
    ...jobCount,
});
