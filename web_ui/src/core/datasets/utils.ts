// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isNil } from 'lodash-es';

import { isNonEmptyString } from '../../shared/utils';
import { JobStep } from '../jobs/jobs.interface';
import { DATASET_IMPORT_DOMAIN, DATASET_IMPORT_STATUSES, DATASET_IMPORT_TASK_TYPE } from './dataset.enum';
import { DatasetImportItem } from './dataset.interface';

export const isPreparingJob = ({ status, preparingJobId }: DatasetImportItem) =>
    status === DATASET_IMPORT_STATUSES.PREPARING && isNonEmptyString(preparingJobId);

export const isImportingNewProjectJob = ({ status, importingJobId }: DatasetImportItem) =>
    status === DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT && isNonEmptyString(importingJobId);

export const isImportingExistingProjectJob = ({ status, importingJobId }: DatasetImportItem) =>
    status === DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT && isNonEmptyString(importingJobId);

export const isImportingJob = (item: DatasetImportItem) =>
    isImportingNewProjectJob(item) || isImportingExistingProjectJob(item);

export const getCurrentJob = (datasetImportItem: DatasetImportItem) => {
    if (isPreparingJob(datasetImportItem)) {
        return String(datasetImportItem.preparingJobId);
    }

    if (isImportingNewProjectJob(datasetImportItem) || isImportingExistingProjectJob(datasetImportItem)) {
        return String(datasetImportItem.importingJobId);
    }
};

export const getJobInfo = (steps: JobStep[] | undefined, defaultMessage: string) => {
    const step = steps?.at(0);

    if (isNil(step)) {
        return { description: `${defaultMessage}`, progress: 0 };
    }

    if (isNil(step.message)) {
        return { description: step.stepName, progress: 0 };
    }

    return { description: `${step.stepName}: ${step.message}`, progress: Number(step.progress) };
};

export const TASK_TYPE_TO_DOMAIN: Record<DATASET_IMPORT_TASK_TYPE, DATASET_IMPORT_DOMAIN | undefined> = {
    [DATASET_IMPORT_TASK_TYPE.ANOMALY_CLASSIFICATION]: DATASET_IMPORT_DOMAIN.ANOMALY_CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE.ANOMALY_DETECTION]: DATASET_IMPORT_DOMAIN.ANOMALY_DETECTION,
    [DATASET_IMPORT_TASK_TYPE.ANOMALY_SEGMENTATION]: DATASET_IMPORT_DOMAIN.ANOMALY_SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE.CLASSIFICATION]: DATASET_IMPORT_DOMAIN.CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE.DETECTION]: DATASET_IMPORT_DOMAIN.DETECTION,
    [DATASET_IMPORT_TASK_TYPE.DETECTION_ROTATED_BOUNDING_BOX]: DATASET_IMPORT_DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
    [DATASET_IMPORT_TASK_TYPE.SEGMENTATION]: DATASET_IMPORT_DOMAIN.SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE.SEGMENTATION_INSTANCE]: DATASET_IMPORT_DOMAIN.SEGMENTATION_INSTANCE,

    [DATASET_IMPORT_TASK_TYPE.DATASET]: undefined,
    [DATASET_IMPORT_TASK_TYPE.CROP]: DATASET_IMPORT_DOMAIN.CROP,

    [DATASET_IMPORT_TASK_TYPE.CLASSIFICATION_HIERARCHICAL]: DATASET_IMPORT_DOMAIN.CLASSIFICATION_HIERARCHICAL,
    [DATASET_IMPORT_TASK_TYPE.DETECTION_CLASSIFICATION]: DATASET_IMPORT_DOMAIN.DETECTION_CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE.DETECTION_SEGMENTATION]: DATASET_IMPORT_DOMAIN.DETECTION_SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE.KEYPOINT_DETECTION]: DATASET_IMPORT_DOMAIN.KEYPOINT_DETECTION,
};
