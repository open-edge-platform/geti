// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DATASET_IMPORT_STATUSES } from '../../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../../core/datasets/dataset.interface';
import { isDetailsAvailable, isErrorStatus, isUploadingStatus } from './util';

describe('utils', () => {
    it('isErrorStatus', () => {
        expect(isErrorStatus({ status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR } as DatasetImportItem)).toBe(true);
        expect(isErrorStatus({ status: DATASET_IMPORT_STATUSES.PREPARING_ERROR } as DatasetImportItem)).toBe(true);
        expect(
            isErrorStatus({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR } as DatasetImportItem)
        ).toBe(true);
        expect(
            isErrorStatus({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR } as DatasetImportItem)
        ).toBe(true);
    });

    it('isUploadingStatus', () => {
        expect(isUploadingStatus({ status: DATASET_IMPORT_STATUSES.UPLOADING } as DatasetImportItem)).toBe(true);
        expect(isUploadingStatus({ status: DATASET_IMPORT_STATUSES.PREPARING } as DatasetImportItem)).toBe(true);
        expect(
            isUploadingStatus({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT } as DatasetImportItem)
        ).toBe(true);
        expect(
            isUploadingStatus({
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
            } as DatasetImportItem)
        ).toBe(true);
    });

    it('isDetailsAvailable', () => {
        expect(isDetailsAvailable({ status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR } as DatasetImportItem)).toBe(
            false
        );
        expect(isDetailsAvailable({ status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED } as DatasetImportItem)).toBe(
            false
        );
        expect(isDetailsAvailable({ status: DATASET_IMPORT_STATUSES.PREPARING_ERROR } as DatasetImportItem)).toBe(
            false
        );
        expect(
            isDetailsAvailable({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT } as DatasetImportItem)
        ).toBe(false);
        expect(
            isDetailsAvailable({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR } as DatasetImportItem)
        ).toBe(false);
        expect(
            isDetailsAvailable({
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            } as DatasetImportItem)
        ).toBe(false);
        expect(
            isDetailsAvailable({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT } as DatasetImportItem)
        ).toBe(false);
        expect(
            isDetailsAvailable({
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
            } as DatasetImportItem)
        ).toBe(false);
    });
});
