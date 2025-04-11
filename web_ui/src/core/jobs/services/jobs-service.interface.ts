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

import { SortDirection } from '../../../shared/components/sort-by-attribute/sort-by-attribute.component';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { JobState, JobType } from '../jobs.const';
import { Job, JobCount } from '../jobs.interface';

export interface JobsQueryParams {
    projectId?: string;
    jobState?: JobState;
    jobTypes?: JobType[];
    key?: string;
    author?: string;
    startTimeFrom?: string;
    startTimeTo?: string;
    skip?: number;
    limit?: number;
    sortDirection?: SortDirection;
}

export interface JobsResponse {
    jobs: Job[];
    jobsCount: JobCount;
    nextPage: NextPageURL;
}

export interface JobsService {
    getJobs(
        workspaceIdentifier: WorkspaceIdentifier,
        queryParams: JobsQueryParams,
        nextPage: NextPageURL
    ): Promise<JobsResponse>;
    cancelJob(workspaceIdentifier: WorkspaceIdentifier, jobId: string): Promise<string>;
    deleteJob(workspaceIdentifier: WorkspaceIdentifier, jobId: string): Promise<string>;
}
