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

import { DATASET_IMPORT_STATUSES } from '../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../core/datasets/dataset.interface';
import { getMockedLabel } from '../../test-utils/mocked-items-factory/mocked-labels';
import { getDatasetImportInitialState, getLabelsMap, matchStatus } from './utils';

describe('import to existing project utils', () => {
    it('matchStatus', () => {
        expect(
            matchStatus(
                { status: DATASET_IMPORT_STATUSES.UPLOADING } as DatasetImportItem,
                DATASET_IMPORT_STATUSES.UPLOADING
            )
        ).toBe(true);

        expect(
            matchStatus({ status: DATASET_IMPORT_STATUSES.UPLOADING } as DatasetImportItem, [
                DATASET_IMPORT_STATUSES.UPLOADING,
                DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
            ])
        ).toBe(true);

        expect(matchStatus(undefined, [DATASET_IMPORT_STATUSES.UPLOADING])).toBe(false);
    });

    it('getDatasetImportInitialState', () => {
        const config = {
            id: 'test',
            name: 'name-test',
            size: 'size-test',
            projectId: 'projectId-test',
            datasetId: 'datasetId-test',
        };

        expect(getDatasetImportInitialState(config)).toEqual({
            bytesRemaining: null,
            datasetName: '',
            labels: [],
            labelsMap: {},
            progress: 0,
            startAt: expect.anything(),
            startFromBytes: 0,
            status: 'uploading',
            timeRemaining: null,
            uploadId: null,
            warnings: [],
            ...config,
        });
    });

    describe('getLabelsMap', () => {
        const labels = ['volvo', 'bmw', 'audi', 'mercedes'];

        it('should NOT do mapping for labels coming from project and from imported dataset if they do not match', () => {
            const projectLabels = [getMockedLabel({ name: 'dog' })];

            expect(getLabelsMap(labels, projectLabels)).toEqual({});
        });

        it('should do mapping for labels coming from project and from imported dataset if they match exactly', () => {
            const projectLabels = [
                getMockedLabel({ name: 'volvo', id: 'volvo-id' }),
                getMockedLabel({ name: 'mercedes', id: 'mercedes-id' }),
            ];

            expect(getLabelsMap(labels, projectLabels)).toEqual({ mercedes: 'mercedes-id', volvo: 'volvo-id' });
        });

        it('should do mapping for labels coming from project and from imported dataset if they match', () => {
            const projectLabels = [
                getMockedLabel({ name: 'Volvo', id: 'volvo-id' }),
                getMockedLabel({ name: 'Mercedes', id: 'mercedes-id' }),
            ];

            expect(getLabelsMap(labels, projectLabels)).toEqual({ mercedes: 'mercedes-id', volvo: 'volvo-id' });
        });
    });
});
