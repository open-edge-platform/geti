// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DATASET_IMPORT_STATUSES } from '../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../core/datasets/dataset.interface';
import { matchStatus } from '../../../providers/dataset-import-to-existing-project-provider/utils';

export const isErrorStatus = (datasetImportItem: DatasetImportItem) => {
    return matchStatus(datasetImportItem, [
        DATASET_IMPORT_STATUSES.IMPORTING_ERROR,
        DATASET_IMPORT_STATUSES.PREPARING_ERROR,
        DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR,
        DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
    ]);
};

export const isUploadingStatus = (datasetImportItem: DatasetImportItem) => {
    return matchStatus(datasetImportItem, [
        DATASET_IMPORT_STATUSES.UPLOADING,
        DATASET_IMPORT_STATUSES.PREPARING,
        DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
        DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
    ]);
};

export const isDetailsAvailable = (datasetImportItem: DatasetImportItem): boolean => {
    return !matchStatus(datasetImportItem, [
        DATASET_IMPORT_STATUSES.IMPORTING_ERROR,
        DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED,

        DATASET_IMPORT_STATUSES.PREPARING_ERROR,

        DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
        DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR,

        DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
        DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
        DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
    ]);
};
