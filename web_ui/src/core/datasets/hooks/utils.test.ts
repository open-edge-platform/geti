// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getMockedJobStep } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { JobState, JobStepState } from '../../jobs/jobs.const';
import { JobDataset } from '../../jobs/jobs.interface';
import { getIntervalJobHandlers } from './utils';

describe('getIntervalJobHandlers', () => {
    const getMockedDatasetJob = (state: JobState) =>
        ({
            state,
            steps: [getMockedJobStep({ state: JobStepState.FAILED, message: null })],
        }) as JobDataset;

    const defaultErrorResponse = {
        message: 'Something went wrong. Please try again',
        response: { status: 501 },
    };
    const mockedHandlers = {
        onError: jest.fn(),
        onSuccess: jest.fn(),
        onSettled: jest.fn(),
        onCancelOrFailed: jest.fn(),
        onCancel: jest.fn(),
    };

    const intervalHandler = getIntervalJobHandlers(mockedHandlers);

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('finished', () => {
        const job = getMockedDatasetJob(JobState.FINISHED);
        intervalHandler(job);

        expect(mockedHandlers.onSuccess).toHaveBeenCalledWith(job);
        expect(mockedHandlers.onSettled).toHaveBeenCalled();
        expect(mockedHandlers.onCancelOrFailed).not.toHaveBeenCalled();
        expect(mockedHandlers.onError).not.toHaveBeenCalled();
    });

    it('cancelled', () => {
        const job = getMockedDatasetJob(JobState.CANCELLED);
        intervalHandler(job);

        expect(mockedHandlers.onCancelOrFailed).toHaveBeenCalled();
        expect(mockedHandlers.onCancel).toHaveBeenCalled();
        expect(mockedHandlers.onSettled).toHaveBeenCalled();
        expect(mockedHandlers.onSuccess).not.toHaveBeenCalled();
    });

    it('failed', () => {
        const job = getMockedDatasetJob(JobState.FAILED);
        intervalHandler(job);

        expect(mockedHandlers.onCancelOrFailed).toHaveBeenCalled();
        expect(mockedHandlers.onSettled).toHaveBeenCalled();
        expect(mockedHandlers.onError).toHaveBeenCalledWith(defaultErrorResponse);
        expect(mockedHandlers.onSuccess).not.toHaveBeenCalled();
    });
});
