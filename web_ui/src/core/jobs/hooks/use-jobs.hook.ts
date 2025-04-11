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

import {
    InfiniteData,
    infiniteQueryOptions,
    QueryKey,
    useInfiniteQuery,
    UseInfiniteQueryOptions,
    UseInfiniteQueryResult,
    useMutation,
    UseMutationResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { useWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { Task } from '../../projects/task.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { JobState, JobType } from '../jobs.const';
import { JobsQueryParams, JobsResponse, JobsService } from '../services/jobs-service.interface';
import { hasJobForCurrentTask, NORMAL_INTERVAL, useInvalidateBalanceOnNewJob } from './utils';

type UseGetJobs = UseInfiniteQueryOptions<JobsResponse, AxiosError, JobsResponse, JobsResponse, QueryKey, NextPageURL>;

interface UseJobs {
    useGetJobs: (
        queryParams?: JobsQueryParams,
        options?: Pick<UseGetJobs, 'enabled' | 'refetchInterval' | 'refetchIntervalInBackground' | 'placeholderData'> &
            Partial<Pick<UseGetJobs, 'queryKey'>>
    ) => UseInfiniteQueryResult<InfiniteData<JobsResponse>>;
    useCancelJob: UseMutationResult<string, AxiosError, string, unknown>;
    useDeleteJob: UseMutationResult<string, AxiosError, string, unknown>;
}

type UseGetScheduledJobs = {
    projectId: string;
    jobTypes?: JobType[];
    queryOptions?: Pick<UseGetJobs, 'enabled' | 'refetchIntervalInBackground'> & Partial<Pick<UseGetJobs, 'queryKey'>>;
};

type UseGetRunningJobs = {
    projectId: string;
    jobTypes?: JobType[];
    selectedTask?: Task | null;
    queryOptions?: Pick<UseGetJobs, 'enabled' | 'refetchIntervalInBackground'> & Partial<Pick<UseGetJobs, 'queryKey'>>;
};

const jobsQueryOptions = ({
    jobsService,
    queryParams,
    workspaceIdentifier,
}: {
    jobsService: JobsService;
    queryParams: JobsQueryParams;
    workspaceIdentifier: WorkspaceIdentifier;
}) => {
    return infiniteQueryOptions<JobsResponse, AxiosError, InfiniteData<JobsResponse>, QueryKey, NextPageURL>({
        queryFn: ({ pageParam: nextPage }) => jobsService.getJobs(workspaceIdentifier, queryParams, nextPage),
        queryKey: QUERY_KEYS.JOBS_KEY(workspaceIdentifier, JSON.stringify(queryParams)),
        meta: { notifyOnError: true },
        getPreviousPageParam: () => undefined,
        notifyOnChangeProps: ['data', 'isPending'],
        initialPageParam: undefined,
        getNextPageParam: ({ nextPage }) => (nextPage === '' ? undefined : nextPage),
    });
};

export const useGetRunningJobs = ({
    projectId,
    jobTypes = [JobType.TRAIN],
    selectedTask = null,
    queryOptions = {},
}: UseGetRunningJobs) => {
    const workspaceIdentifier = useWorkspaceIdentifier();
    const { jobsService } = useApplicationServices();

    const REFETCH_INTERVAL_NO_TRAINING = 5_000;
    const REFETCH_INTERVAL_TRAINING = 30_000;
    const queryParams = {
        jobTypes,
        jobState: JobState.RUNNING,
        projectId,
    };

    const query = useInfiniteQuery({
        ...jobsQueryOptions({ jobsService, queryParams, workspaceIdentifier }),
        refetchInterval: (jobsQuery) => {
            const hasTrainingJob = jobsQuery.state.data?.pages.some(({ jobs }) =>
                hasJobForCurrentTask(jobs, selectedTask)
            );

            return hasTrainingJob ? REFETCH_INTERVAL_TRAINING : REFETCH_INTERVAL_NO_TRAINING;
        },
        ...queryOptions,
    });

    useInvalidateBalanceOnNewJob(workspaceIdentifier, query.data, queryParams);

    return query;
};

export const useGetScheduledJobs = ({
    projectId,
    queryOptions = {},
    jobTypes = [JobType.TRAIN],
}: UseGetScheduledJobs) => {
    const workspaceIdentifier = useWorkspaceIdentifier();
    const { jobsService } = useApplicationServices();

    const queryParams = {
        jobTypes,
        jobState: JobState.SCHEDULED,
        projectId,
    };

    const query = useInfiniteQuery({
        ...jobsQueryOptions({ jobsService, queryParams, workspaceIdentifier }),
        refetchInterval: (jobsQuery) => {
            const hasScheduledJobs = jobsQuery.state.data?.pages.some(({ jobs }) => jobs.length > 0);

            return hasScheduledJobs ? NORMAL_INTERVAL : false;
        },
        ...queryOptions,
    });

    useInvalidateBalanceOnNewJob(workspaceIdentifier, query.data, queryParams);

    return query;
};

export const useJobs = (workspaceIdentifier: WorkspaceIdentifier): UseJobs => {
    const { addNotification } = useNotification();
    const { jobsService } = useApplicationServices();

    const onError = (error: AxiosError) => {
        addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
    };

    const useGetJobs: UseJobs['useGetJobs'] = (queryParams = {}, options = {}) => {
        const query = useInfiniteQuery({
            ...jobsQueryOptions({ jobsService, queryParams, workspaceIdentifier }),
            ...options,
        });

        useInvalidateBalanceOnNewJob(workspaceIdentifier, query.data, queryParams);

        return query;
    };

    const useCancelJob = useMutation({
        mutationFn: (jobId: string) => jobsService.cancelJob(workspaceIdentifier, jobId),
        onError,
    });

    const useDeleteJob = useMutation({
        mutationFn: (jobId: string) => jobsService.deleteJob(workspaceIdentifier, jobId),
        onError,
    });

    return { useGetJobs, useCancelJob, useDeleteJob };
};
