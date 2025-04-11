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

import { AxiosResponse } from 'axios';

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { JobsResponseDTO } from '../dtos/jobs-dto.interface';
import { getJobCountEntity, getJobEntity } from '../utils';
import { JobsQueryParams, JobsResponse, JobsService } from './jobs-service.interface';

export const createApiJobsService: CreateApiService<JobsService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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
