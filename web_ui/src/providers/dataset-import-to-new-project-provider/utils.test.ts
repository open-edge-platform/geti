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

import {
    DATASET_IMPORT_STATUSES,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
    DATASET_IMPORT_WARNING_TYPE,
} from '../../core/datasets/dataset.enum';
import { getFileSize } from '../../shared/utils';
import {
    formatDatasetPrepareImportResponse,
    getBytesRemaining,
    getDatasetImportInitialState,
    getTimeRemaining,
} from './utils';

jest.mock('../../shared/utils', () => ({
    ...jest.requireActual('../../shared/utils'),
    getFileSize: jest.fn(),
}));

describe('import to new project utils', () => {
    it('getDatasetImportInitialState', () => {
        const initData = { id: 'id-test', name: 'name-test', size: 'size-test' };
        expect(getDatasetImportInitialState(initData)).toEqual(
            expect.objectContaining({
                ...initData,
                status: DATASET_IMPORT_STATUSES.UPLOADING,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
                openedSteps: [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET],
            })
        );
    });

    it('getBytesRemaining', () => {
        const mockedValue = 'test-time';
        jest.mocked(getFileSize).mockReturnValue(mockedValue);

        expect(getBytesRemaining(20)).toBe(`${mockedValue} left`);
        expect(getBytesRemaining(0)).toBe(``);
    });

    describe('formatDatasetPrepareImportResponse', () => {
        it('empty warnings', () => {
            const initData = {
                id: 'id-test',
                uploadId: 'uploadId-test',
                warnings: [],
                supportedProjectTypes: [],
            };
            expect(formatDatasetPrepareImportResponse(initData)).toEqual({
                ...initData,
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN,
                completedSteps: [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET],
                openedSteps: [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET, DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN],
            });
        });

        it('warnings', () => {
            const initData = {
                id: 'id-test',
                uploadId: 'uploadId-test',
                supportedProjectTypes: [],
                warnings: [
                    {
                        name: 'warning-test',
                        description: 'description-test',
                        type: DATASET_IMPORT_WARNING_TYPE.WARNING,
                    },
                ],
            };
            expect(formatDatasetPrepareImportResponse(initData)).toEqual({
                ...initData,
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
                openedSteps: [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET],
                completedSteps: [],
            });
        });
    });

    describe('getTimeRemaining', () => {
        it('zero remaining bytes', () => {
            expect(getTimeRemaining(Date.now() - 10, 0, 100)).toEqual('');
        });

        it('10 remaining bytes', () => {
            expect(getTimeRemaining(Date.now() - 10, 90, 100)).toEqual('a few seconds left');
        });

        it('calculating', () => {
            expect(getTimeRemaining(Date.now(), 0, 0)).toEqual('Calculating...');
        });
    });
});
