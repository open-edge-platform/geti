// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useRef } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { InfiniteData, useQueryClient } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { useGetRunningJobs, useGetScheduledJobs } from '../../../../../../core/jobs/hooks/use-jobs.hook';
import { JobState } from '../../../../../../core/jobs/jobs.const';
import { RunningTrainingJob } from '../../../../../../core/jobs/jobs.interface';
import { JobsResponse } from '../../../../../../core/jobs/services/jobs-service.interface';
import { useProjectIdentifier } from '../../../../../../hooks/use-project-identifier/use-project-identifier';
import {
    getAllJobs,
    isRunningOrScheduledTrainingJob,
} from '../../../../../../shared/components/header/jobs-management/utils';

interface UseTrainingProgressDetails {
    showTrainingProgress: true;
    trainingDetails: RunningTrainingJob[];
}

interface UseTrainingProgressNoDetails {
    showTrainingProgress: false;
}

type UseTrainingProgress = UseTrainingProgressDetails | UseTrainingProgressNoDetails;

const useTrainingProgressJobs = () => {
    const queryClient = useQueryClient();
    const projectIdentifier = useProjectIdentifier();
    const prevJobsSize = useRef<number>();
    const areTrainingDetails = true;

    const handleSuccess = useCallback(
        async (jobsResponse: InfiniteData<JobsResponse>) => {
            const jobs = getAllJobs(jobsResponse);

            if (prevJobsSize.current !== jobs.length) {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.MODELS_KEY(projectIdentifier) });

                prevJobsSize.current = jobs.length;
            }
        },
        [queryClient, projectIdentifier]
    );

    const { data: runningJobsData, isSuccess: runningJobsIsSuccess } = useGetRunningJobs({
        projectId: projectIdentifier.projectId,
        queryOptions: {
            refetchIntervalInBackground: true,
            queryKey: QUERY_KEYS.JOBS_KEY(projectIdentifier, JobState.RUNNING, areTrainingDetails),
        },
    });

    const { data: scheduledJobsData, isSuccess: scheduledJobsIsSuccess } = useGetScheduledJobs({
        projectId: projectIdentifier.projectId,
        queryOptions: {
            refetchIntervalInBackground: true,
            queryKey: QUERY_KEYS.JOBS_KEY(projectIdentifier, JobState.SCHEDULED, areTrainingDetails),
        },
    });

    useEffect(() => {
        if (!runningJobsIsSuccess && !scheduledJobsIsSuccess) {
            return;
        }

        handleSuccess({
            pages: [...(runningJobsData?.pages ?? []), ...(scheduledJobsData?.pages ?? [])],
            pageParams: [...(runningJobsData?.pageParams ?? []), ...(scheduledJobsData?.pageParams ?? [])],
        });
    }, [runningJobsData, runningJobsIsSuccess, handleSuccess, scheduledJobsData, scheduledJobsIsSuccess]);

    const runningJobs = runningJobsData?.pages?.flatMap((jobsResponse) => jobsResponse.jobs) ?? [];
    const scheduledJobs = scheduledJobsData?.pages?.flatMap((jobsResponse) => jobsResponse.jobs) ?? [];

    return [...runningJobs, ...scheduledJobs];
};

export const useTrainingProgress = (taskId: string): UseTrainingProgress => {
    const data = useTrainingProgressJobs();

    const getTrainingDetails = (): RunningTrainingJob[] => {
        const jobsPerTask = data.filter(
            (job) => isRunningOrScheduledTrainingJob(job) && taskId === job.metadata.task.taskId
        ) as RunningTrainingJob[];
        return jobsPerTask;
    };

    const trainingDetails = getTrainingDetails();

    if (!isEmpty(trainingDetails)) {
        return {
            showTrainingProgress: true,
            trainingDetails,
        };
    }

    return {
        showTrainingProgress: false,
    };
};
