// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DATASET_IMPORT_STATUSES } from '../../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../../core/datasets/dataset.interface';
import { paths } from '../../../../core/services/routes';
import { isNonEmptyString } from '../../../../shared/utils';

export enum DatasetChapters {
    DEFAULT = '',
    MEDIA = 'media',
    STATISTICS = 'statistics',
}

export const DATASET_TABS_TO_PATH = {
    [DatasetChapters.DEFAULT]: paths.project.dataset.index,
    [DatasetChapters.MEDIA]: paths.project.dataset.media,
    [DatasetChapters.STATISTICS]: paths.project.dataset.statistics,
};

export enum DatasetTabActions {
    ImportDataset = 'Import dataset',
    ExportDataset = 'Export dataset',
    DeleteDataset = 'Delete dataset',
    UpdateDataset = 'Edit dataset name',
}

export const DATASET_NAME_MAX_WIDTH = 160;

export const MAX_NUMBER_OF_DISPLAYED_DATASETS = 6; // Default dataset + 5 testing datasets

export const NO_MEDIA_MESSAGE = 'You have to upload images or videos';

export const isImportingValidJob = ({ status, importingJobId }: DatasetImportItem) =>
    status === DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT && isNonEmptyString(importingJobId);

export const getDatasetButtonActions = (hasMediaItems: boolean, isTaskChainProject: boolean): DatasetTabActions[] => {
    const actions: DatasetTabActions[] = [];

    if (hasMediaItems) {
        actions.push(DatasetTabActions.ExportDataset);
    }

    if (!isTaskChainProject) {
        actions.push(DatasetTabActions.ImportDataset);
    }

    return actions;
};

export const getDatasetTabActions = ({
    hasMediaItems,
    isTrainingDatasetSelected,
    isTaskChainProject,
}: {
    hasMediaItems: boolean;
    isTaskChainProject: boolean;
    isTrainingDatasetSelected: boolean;
}): DatasetTabActions[] => {
    const actions: DatasetTabActions[] = getDatasetButtonActions(hasMediaItems, isTaskChainProject);

    if (!isTrainingDatasetSelected) {
        actions.push(DatasetTabActions.DeleteDataset, DatasetTabActions.UpdateDataset);
    }

    return actions;
};
