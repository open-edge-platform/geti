// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
