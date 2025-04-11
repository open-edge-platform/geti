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

import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
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
