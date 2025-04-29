// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
