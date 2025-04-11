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

import { DATASET_IMPORT_STATUSES } from '../../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../../core/datasets/dataset.interface';
import { DatasetTabActions, getDatasetButtonActions, getDatasetTabActions, isImportingValidJob } from './utils';

const getMockedDatasetImportItem = (status: DATASET_IMPORT_STATUSES, importingJobId?: string | null) =>
    ({
        status,
        importingJobId,
    }) as DatasetImportItem;

describe('project dataset utils', () => {
    it('isImportingValidJob', () => {
        expect(
            isImportingValidJob(
                getMockedDatasetImportItem(DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT, '123')
            )
        ).toBe(true);

        expect(
            isImportingValidJob(getMockedDatasetImportItem(DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT, null))
        ).toBe(false);

        expect(
            isImportingValidJob(
                getMockedDatasetImportItem(DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT, undefined)
            )
        ).toBe(false);

        expect(
            isImportingValidJob(getMockedDatasetImportItem(DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT, '123'))
        ).toBe(false);
    });

    it('getDatasetButtonActions', () => {
        expect(getDatasetButtonActions(false, false)).toEqual([DatasetTabActions.ImportDataset]);

        expect(getDatasetButtonActions(true, false)).toEqual([
            DatasetTabActions.ExportDataset,
            DatasetTabActions.ImportDataset,
        ]);

        expect(getDatasetButtonActions(false, true)).toEqual([]);

        expect(getDatasetButtonActions(true, true)).toEqual([DatasetTabActions.ExportDataset]);
    });

    it('getDatasetTabActions', () => {
        expect(
            getDatasetTabActions({ hasMediaItems: false, isTaskChainProject: false, isTrainingDatasetSelected: false })
        ).toEqual([DatasetTabActions.ImportDataset, DatasetTabActions.DeleteDataset, DatasetTabActions.UpdateDataset]);

        expect(
            getDatasetTabActions({ hasMediaItems: false, isTaskChainProject: false, isTrainingDatasetSelected: true })
        ).toEqual([DatasetTabActions.ImportDataset]);

        expect(
            getDatasetTabActions({ hasMediaItems: false, isTaskChainProject: true, isTrainingDatasetSelected: false })
        ).toEqual([DatasetTabActions.DeleteDataset, DatasetTabActions.UpdateDataset]);

        expect(
            getDatasetTabActions({ hasMediaItems: false, isTaskChainProject: true, isTrainingDatasetSelected: true })
        ).toEqual([]);

        expect(
            getDatasetTabActions({ hasMediaItems: true, isTaskChainProject: true, isTrainingDatasetSelected: true })
        ).toEqual([DatasetTabActions.ExportDataset]);

        expect(
            getDatasetTabActions({ hasMediaItems: true, isTaskChainProject: true, isTrainingDatasetSelected: false })
        ).toEqual([DatasetTabActions.ExportDataset, DatasetTabActions.DeleteDataset, DatasetTabActions.UpdateDataset]);

        expect(
            getDatasetTabActions({ hasMediaItems: true, isTaskChainProject: false, isTrainingDatasetSelected: true })
        ).toEqual([DatasetTabActions.ExportDataset, DatasetTabActions.ImportDataset]);

        expect(
            getDatasetTabActions({ hasMediaItems: true, isTaskChainProject: false, isTrainingDatasetSelected: false })
        ).toEqual([
            DatasetTabActions.ExportDataset,
            DatasetTabActions.ImportDataset,
            DatasetTabActions.DeleteDataset,
            DatasetTabActions.UpdateDataset,
        ]);
    });
});
