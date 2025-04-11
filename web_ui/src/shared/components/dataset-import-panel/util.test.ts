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
