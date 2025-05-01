// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SortDirection } from '@shared/components/sort-by-attribute/sort-by-attribute.component';

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
