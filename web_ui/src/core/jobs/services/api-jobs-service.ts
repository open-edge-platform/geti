// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';
import { AxiosResponse } from 'axios';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../../../packages/core/src/services/urls';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { JobsResponseDTO } from '../dtos/jobs-dto.interface';
import { getJobCountEntity, getJobEntity } from '../utils';
import { JobsQueryParams, JobsResponse, JobsService } from './jobs-service.interface';

export const createApiJobsService: CreateApiService<JobsService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getJobs = async (
        workspaceIdentifier: WorkspaceIdentifier,
        queryParams: JobsQueryParams,
        nextPage: string | undefined
    ): Promise<JobsResponse> => {
        const url: string = nextPage ?? router.JOBS_QUERY_PARAMS(workspaceIdentifier, queryParams);

        const { data }: AxiosResponse<JobsResponseDTO> = await instance.get<JobsResponseDTO>(url);

        return {
            jobs: data.jobs.map(getJobEntity),
            jobsCount: getJobCountEntity(data.jobs_count),
            nextPage: data.next_page,
        };
    };

    const cancelJob = async (workspaceIdentifier: WorkspaceIdentifier, jobId: string): Promise<string> => {
        const url: string = router.JOB_CANCEL(workspaceIdentifier, jobId);
        const { data } = await instance.post(url);

        return data;
    };

    const deleteJob = async (workspaceIdentifier: WorkspaceIdentifier, jobId: string): Promise<string> => {
        const url: string = router.JOB(workspaceIdentifier, jobId);
        const { data } = await instance.delete(url);

        return data;
    };

    return { getJobs, cancelJob, deleteJob };
};
