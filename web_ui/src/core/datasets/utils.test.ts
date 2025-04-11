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

import { JobStepState } from '../jobs/jobs.const';
import { DATASET_IMPORT_STATUSES } from './dataset.enum';
import { DatasetImportItem } from './dataset.interface';
import {
    getCurrentJob,
    getJobInfo,
    isImportingExistingProjectJob,
    isImportingNewProjectJob,
    isPreparingJob,
} from './utils';

const getMockedImportItem = (data: Partial<DatasetImportItem> = {}): DatasetImportItem => ({
    id: '987-654-321',
    name: 'Test Dataset',
    size: '1Gb',
    status: DATASET_IMPORT_STATUSES.UPLOADING,
    progress: 50,
    startAt: 0,
    startFromBytes: 0,
    uploadId: '192-837-465',
    bytesRemaining: '500Mb',
    timeRemaining: '10 minutes',
    warnings: [],
    ...data,
});

describe('datasets utils', () => {
    it('isPreparingJob', () => {
        expect(
            isPreparingJob(getMockedImportItem({ status: DATASET_IMPORT_STATUSES.PREPARING, preparingJobId: '123' }))
        ).toBe(true);

        expect(
            isPreparingJob(getMockedImportItem({ status: DATASET_IMPORT_STATUSES.PREPARING, preparingJobId: '' }))
        ).toBe(false);

        expect(
            isPreparingJob(
                getMockedImportItem({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT, preparingJobId: '123' })
            )
        ).toBe(false);
    });

    it('isImportingNewProjectJob', () => {
        expect(
            isImportingNewProjectJob(
                getMockedImportItem({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT, importingJobId: '123' })
            )
        ).toBe(true);

        expect(
            isImportingNewProjectJob(
                getMockedImportItem({ status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT, importingJobId: '' })
            )
        ).toBe(false);

        expect(
            isImportingNewProjectJob(
                getMockedImportItem({
                    status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                    importingJobId: '123',
                })
            )
        ).toBe(false);
    });

    it('isImportingExistingProjectJob', () => {
        expect(
            isImportingExistingProjectJob(
                getMockedImportItem({
                    status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                    importingJobId: '123',
                })
            )
        ).toBe(true);

        expect(
            isImportingExistingProjectJob(
                getMockedImportItem({
                    status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                    importingJobId: '',
                })
            )
        ).toBe(false);

        expect(
            isImportingExistingProjectJob(
                getMockedImportItem({
                    status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
                    importingJobId: '123',
                })
            )
        ).toBe(false);
    });

    describe('getCurrentJob', () => {
        const importingJobId = '123';
        const preparingJobId = '321';

        it('importingJobId', () => {
            expect(
                getCurrentJob(
                    getMockedImportItem({
                        status: DATASET_IMPORT_STATUSES.PREPARING,
                        preparingJobId,
                    })
                )
            ).toBe(preparingJobId);
        });

        it('preparingJobId', () => {
            expect(
                getCurrentJob(
                    getMockedImportItem({
                        status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                        importingJobId,
                    })
                )
            ).toBe(importingJobId);

            expect(
                getCurrentJob(
                    getMockedImportItem({
                        status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
                        importingJobId,
                    })
                )
            ).toBe(importingJobId);
        });

        it('others', () => {
            expect(
                getCurrentJob(
                    getMockedImportItem({
                        status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
                        importingJobId,
                    })
                )
            ).toBe(undefined);
        });
    });
    it('getJobInfo', () => {
        const mockedStep = {
            index: 1,
            progress: 10,
            message: 'mocked step message',
            state: JobStepState.RUNNING,
            stepName: 'Test step',
        };

        const defaultMessage = 'Preparing...';

        expect(getJobInfo(undefined, defaultMessage)).toEqual({
            description: defaultMessage,
            progress: 0,
        });

        expect(getJobInfo([{ ...mockedStep, message: null }], defaultMessage)).toEqual({
            description: mockedStep.stepName,
            progress: 0,
        });
        expect(getJobInfo([mockedStep], defaultMessage)).toEqual({
            description: `${mockedStep.stepName}: ${mockedStep.message}`,
            progress: mockedStep.progress,
        });
    });
});
