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
