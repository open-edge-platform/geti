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

import { rest } from 'msw';

import { getMockedWorkspaceIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { server } from '../../annotations/services/test-utils';
import { apiRequestUrl } from '../../services/test-utils';
import { API_URLS } from '../../services/urls';
import { createInMemoryJobsService } from './in-memory-jobs-service';
import { JobsResponse } from './jobs-service.interface';

describe('Api jobs service', () => {
    const jobsService = createInMemoryJobsService();
    const workspaceIdentifier = getMockedWorkspaceIdentifier({ workspaceId: 'workspaceId' });

    it('Get jobs', async (): Promise<void> => {
        const getJobsUrl: string = API_URLS.JOBS_QUERY_PARAMS(workspaceIdentifier, {});
        const mockResponse = {
            jobs: [],
            jobsCount: {
                numberOfRunningJobs: 0,
                numberOfFinishedJobs: 0,
                numberOfScheduledJobs: 0,
                numberOfCancelledJobs: 0,
                numberOfFailedJobs: 0,
            },
            nextPage: '',
        };

        server.use(rest.get(apiRequestUrl(getJobsUrl), (_req, res, ctx) => res(ctx.status(200))));
        const response: JobsResponse = await jobsService.getJobs(workspaceIdentifier, {}, undefined);

        expect(response).toEqual(mockResponse);
    });

    it('Delete job', async (): Promise<void> => {
        const deleteJobsUrl: string = API_URLS.JOB(workspaceIdentifier, 'jobId');

        server.use(rest.post(apiRequestUrl(deleteJobsUrl), (_req, res, ctx) => res(ctx.status(200))));
        const response: string = await jobsService.deleteJob(workspaceIdentifier, 'jobId');

        expect(response).toEqual('');
    });

    it('Cancel job', async (): Promise<void> => {
        const cancelJobsUrl: string = API_URLS.JOB_CANCEL(workspaceIdentifier, 'jobId');

        server.use(rest.post(apiRequestUrl(cancelJobsUrl), (_req, res, ctx) => res(ctx.status(200))));
        const response: string = await jobsService.cancelJob(workspaceIdentifier, 'jobId');

        expect(response).toEqual('');
    });
});
