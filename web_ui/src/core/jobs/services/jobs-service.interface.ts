// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceIdentifier } from '../../../../packages/core/src/workspaces/services/workspaces.interface';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { SortDirection } from '../../shared/query-parameters';
import { JobState, JobType } from '../jobs.const';
import { Job, JobCount } from '../jobs.interface';

export interface JobsQueryParams {
    projectId?: string;
    jobState?: JobState;
    jobTypes?: JobType[];
    key?: string;
    author?: string;
    creationTimeFrom?: string;
    creationTimeTo?: string;
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
