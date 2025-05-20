// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useRef } from 'react';

import { InfiniteData, useQueryClient } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { useGetRunningJobs, useGetScheduledJobs } from '../../../../../../core/jobs/hooks/use-jobs.hook';
import { JobState } from '../../../../../../core/jobs/jobs.const';
import { RunningTrainingJob } from '../../../../../../core/jobs/jobs.interface';
import { JobsResponse } from '../../../../../../core/jobs/services/jobs-service.interface';
import QUERY_KEYS from '../../../../../../core/requests/query-keys';
import { useProjectIdentifier } from '../../../../../../hooks/use-project-identifier/use-project-identifier';
import {
    getAllJobs,
    isRunningOrScheduledTrainingJob,
} from '../../../../../../shared/components/header/jobs-management/utils';
import { useIsTraining } from '../../hooks/use-is-training.hook';

interface UseTrainingProgressDetails {
    showTrainingProgress: true;
    trainingDetails: RunningTrainingJob[];
}

interface UseTrainingProgressNoDetails {
    showTrainingProgress: false;
}

type UseTrainingProgress = UseTrainingProgressDetails | UseTrainingProgressNoDetails;

const useTrainingProgressJobs = (isTraining: boolean) => {
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
            enabled: isTraining,
            refetchIntervalInBackground: true,
            queryKey: QUERY_KEYS.JOBS_KEY(projectIdentifier, JobState.RUNNING, areTrainingDetails),
        },
    });

    const { data: scheduledJobsData, isSuccess: scheduledJobsIsSuccess } = useGetScheduledJobs({
        projectId: projectIdentifier.projectId,
        queryOptions: {
            enabled: isTraining,
            refetchIntervalInBackground: true,
            queryKey: QUERY_KEYS.JOBS_KEY(projectIdentifier, JobState.SCHEDULED, areTrainingDetails),
        },
    });

    useEffect(() => {
        if (!runningJobsIsSuccess || !scheduledJobsIsSuccess) {
            return;
        }

        handleSuccess({...runningJobsData, ...scheduledJobsData });
    }, [runningJobsData, runningJobsIsSuccess, handleSuccess, scheduledJobsData, scheduledJobsIsSuccess]);

    return {...runningJobsData, ...scheduledJobsData};
};

export const useTrainingProgress = (taskId: string): UseTrainingProgress => {
    const isTraining = useIsTraining();
    const data = useTrainingProgressJobs(isTraining);
    
    const getTrainingDetails = (): RunningTrainingJob[] | undefined => {
        const jobs = data?.pages?.flatMap((jobsResponse) => jobsResponse.jobs) ?? [];
        const jobsPerTask = jobs.filter(
            (job) =>
                isRunningOrScheduledTrainingJob(job) &&
                taskId === job.metadata.task.taskId
        ) as RunningTrainingJob[];
        return !isEmpty(jobsPerTask) ? jobsPerTask : undefined;
    };

    const trainingDetails = getTrainingDetails();

    if (isTraining && trainingDetails) {
        return {
            showTrainingProgress: true,
            trainingDetails,
        };
    }

    return {
        showTrainingProgress: false,
    };
};
