// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration.js';
import relativeTime from 'dayjs/plugin/relativeTime.js';
import { isEmpty } from 'lodash-es';

import {
    DATASET_IMPORT_STATUSES,
    DATASET_IMPORT_TASK_TYPE,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
} from '../../core/datasets/dataset.enum';
import {
    DatasetImportSupportedProjectType,
    DatasetImportToNewProjectItem,
    DatasetImportWarning,
} from '../../core/datasets/dataset.interface';
import { getFileSize } from '../../shared/utils';

export const getDatasetImportInitialState = (data: {
    id: string;
    name: string;
    size: string;
}): DatasetImportToNewProjectItem => ({
    ...data,
    labels: [],
    progress: 0,
    warnings: [],
    uploadId: null,
    taskType: null,
    projectName: '',
    startFromBytes: 0,
    startAt: Date.now(),
    timeRemaining: null,
    bytesRemaining: null,
    supportedProjectTypes: [],
    firstChainTaskType: null,
    firstChainLabels: [],
    labelsToSelect: [],
    labelColorMap: {},
    completedSteps: [],
    preparingJobId: null,
    status: DATASET_IMPORT_STATUSES.UPLOADING,
    activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
    openedSteps: [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET],
});

export const formatDatasetPrepareImportResponse = (data: {
    id: string;
    uploadId: string;
    warnings: DatasetImportWarning[];
    supportedProjectTypes: DatasetImportSupportedProjectType[];
}): Partial<DatasetImportToNewProjectItem> => {
    const isEmptyWarnings = isEmpty(data.warnings);
    return {
        ...data,
        status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
        activeStep: isEmptyWarnings
            ? DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN
            : DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
        completedSteps: isEmptyWarnings ? [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET] : [],
        openedSteps: isEmptyWarnings
            ? [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET, DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN]
            : [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET],
    };
};

export const getTimeRemaining = (timeStarted: number, bytesUploaded: number, bytesRemaining: number): string => {
    dayjs.extend(duration);
    dayjs.extend(relativeTime);

    const timeElapsed = Date.now() - timeStarted;
    const uploadSpeed = bytesUploaded / timeElapsed;
    const timeRemaining = Math.floor(bytesRemaining / uploadSpeed);

    if (timeRemaining === undefined || Number.isNaN(timeRemaining)) return 'Calculating...';

    return !!timeRemaining && timeRemaining !== Infinity
        ? `${dayjs.duration(timeRemaining, 'milliseconds').humanize()} left`
        : '';
};

export const getBytesRemaining = (bytesRemaining: number): string =>
    bytesRemaining ? `${getFileSize(bytesRemaining)} left` : '';

export const hasKeypointStructure = (supportedProjectTypes: DatasetImportSupportedProjectType[]) => {
    return supportedProjectTypes.some(
        ({ projectType, pipeline }) =>
            projectType === DATASET_IMPORT_TASK_TYPE.KEYPOINT_DETECTION &&
            pipeline.tasks.some((task) => !isEmpty(task.keypointStructure))
    );
};
