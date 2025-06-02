// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceIdentifier } from '../../../../packages/core/src/workspaces/services/workspaces.interface';
import { JobsResponse, JobsService } from './jobs-service.interface';

export const createInMemoryJobsService = (): JobsService => {
    const getJobs = async (): Promise<JobsResponse> => {
        return Promise.resolve({
            jobs: [],
            jobsCount: {
                numberOfRunningJobs: 0,
                numberOfFinishedJobs: 0,
                numberOfScheduledJobs: 0,
                numberOfCancelledJobs: 0,
                numberOfFailedJobs: 0,
            },
            nextPage: '',
        });
    };

    const cancelJob = async (_workspaceIdentifier: WorkspaceIdentifier, _jobId: string): Promise<string> => {
        return Promise.resolve('');
    };

    const deleteJob = async (_workspaceIdentifier: WorkspaceIdentifier, _jobId: string): Promise<string> => {
        return Promise.resolve('');
    };

    return { getJobs, cancelJob, deleteJob };
};
