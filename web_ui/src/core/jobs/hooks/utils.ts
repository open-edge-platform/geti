// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { InfiniteData, useQueryClient } from '@tanstack/react-query';
import { xor } from 'lodash-es';

import { useFeatureFlags } from '../../feature-flags/hooks/use-feature-flags.hook';
import { Task } from '../../projects/task.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { JobState } from '../jobs.const';
import { Job } from '../jobs.interface';
import { JobsQueryParams, JobsResponse } from '../services/jobs-service.interface';
import { isJobTrain } from '../utils';

export const FAST_INTERVAL = 1000;
export const NORMAL_INTERVAL = 3000;
export const SLOW_INTERVAL = 10000;

type JobsIds = Record<JobState.SCHEDULED | JobState.FAILED | JobState.CANCELLED, string[]>;

export const hasJobForCurrentTask = (jobs: Job[], selectedTask: Task | null) => {
    if (selectedTask !== null) {
        return jobs.some((job) => isJobTrain(job) && job.metadata.task.taskId === selectedTask.id);
    }

    return jobs.length > 0;
};

export const useInvalidateBalanceOnNewJob = (
    workspaceIdentifier: WorkspaceIdentifier,
    data: InfiniteData<JobsResponse> | undefined,
    queryParams: JobsQueryParams
) => {
    const queryClient = useQueryClient();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const prevJobsIds = useRef<JobsIds>({
        [JobState.SCHEDULED]: [],
        [JobState.FAILED]: [],
        [JobState.CANCELLED]: [],
    });

    useEffect(() => {
        if (
            FEATURE_FLAG_CREDIT_SYSTEM &&
            queryParams.jobState !== JobState.RUNNING &&
            queryParams.jobState !== JobState.FINISHED &&
            data
        ) {
            const jobs = data.pages.flatMap((page) => page.jobs).filter((job) => job.cost);

            for (const jobState of (queryParams.jobState
                ? [queryParams.jobState]
                : [JobState.SCHEDULED, JobState.FAILED, JobState.CANCELLED]) as (keyof JobsIds)[]) {
                const jobIds = jobs.filter((job) => job.state === jobState).map((job) => job.id);

                if (xor(jobIds, prevJobsIds.current[jobState]).length) {
                    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ORGANIZATION_BALANCE(workspaceIdentifier) });
                    prevJobsIds.current[jobState] = jobIds;
                }
            }
        }
    }, [FEATURE_FLAG_CREDIT_SYSTEM, data, queryClient, queryParams.jobState, workspaceIdentifier]);
};
