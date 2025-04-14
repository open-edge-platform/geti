// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { getMockedWorkspaceIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedJob } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { JobState, JobType } from '../jobs.const';
import { createInMemoryJobsService } from '../services/in-memory-jobs-service';
import { JobsResponse, JobsService } from '../services/jobs-service.interface';
import { useJobs } from './use-jobs.hook';

const jobsService: JobsService = createInMemoryJobsService();
const workspaceIdentifier = getMockedWorkspaceIdentifier({ workspaceId: 'workspaceId' });

const mockedResponse = {
    pages: [
        {
            nextPage: '',
            jobs: [getMockedJob()],
            jobsCount: {
                numberOfRunningJobs: 0,
                numberOfFinishedJobs: 0,
                numberOfScheduledJobs: 0,
                numberOfCancelledJobs: 0,
                numberOfFailedJobs: 0,
            },
        },
    ],
    pageParams: [undefined],
};

describe('Use jobs hook', (): void => {
    beforeEach(() => {
        jest.resetAllMocks();
    });

    it('should get all jobs', async (): Promise<void> => {
        jobsService.getJobs = jest.fn(
            (): Promise<JobsResponse> =>
                Promise.resolve({
                    jobs: [getMockedJob()],
                    jobsCount: {
                        numberOfRunningJobs: 0,
                        numberOfFinishedJobs: 0,
                        numberOfScheduledJobs: 0,
                        numberOfCancelledJobs: 0,
                        numberOfFailedJobs: 0,
                    },
                    nextPage: '',
                })
        );

        const { result } = renderHookWithProviders(
            () =>
                useJobs(workspaceIdentifier).useGetJobs({
                    jobState: JobState.RUNNING,
                    jobTypes: [JobType.OPTIMIZATION_POT],
                    author: 'admin@example.com',
                }),
            { providerProps: { jobsService } }
        );

        await waitFor(() => expect(result.current.data).toEqual(mockedResponse));

        expect(jobsService.getJobs).toHaveBeenCalledWith(
            workspaceIdentifier,
            { jobState: 'running', jobTypes: ['optimize_pot'], author: 'admin@example.com' },
            undefined
        );
    });

    it('should delete the job', async (): Promise<void> => {
        jobsService.deleteJob = jest.fn((): Promise<string> => Promise.resolve(''));

        const { result } = renderHookWithProviders(() => useJobs(workspaceIdentifier), {
            providerProps: { jobsService },
        });

        result.current.useDeleteJob.mutate('jobId');

        await waitFor(() => {
            expect(jobsService.deleteJob).toHaveBeenCalledWith(workspaceIdentifier, 'jobId');
        });
    });

    it('should cancel the job', async (): Promise<void> => {
        jobsService.cancelJob = jest.fn((): Promise<string> => Promise.resolve(''));

        const { result } = renderHookWithProviders(() => useJobs(workspaceIdentifier), {
            providerProps: { jobsService },
        });

        result.current.useCancelJob.mutate('jobId');
        await waitFor(() => {
            expect(jobsService.cancelJob).toHaveBeenCalledWith(workspaceIdentifier, 'jobId');
        });
    });
});
