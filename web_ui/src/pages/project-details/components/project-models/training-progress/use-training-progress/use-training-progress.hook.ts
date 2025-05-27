// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useRef } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { InfiniteData, useQueryClient } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { useGetRunningJobs } from '../../../../../../core/jobs/hooks/use-jobs.hook';
import { JobState } from '../../../../../../core/jobs/jobs.const';
import { RunningTrainingJob } from '../../../../../../core/jobs/jobs.interface';
import { JobsResponse } from '../../../../../../core/jobs/services/jobs-service.interface';
import { useProjectIdentifier } from '../../../../../../hooks/use-project-identifier/use-project-identifier';
import { getAllJobs, isRunningTrainingJob } from '../../../../../../shared/components/header/jobs-management/utils';
import { useIsTraining } from '../../hooks/use-is-training.hook';

interface UseTrainingProgressDetails {
    showTrainingProgress: true;
    trainingDetails: RunningTrainingJob;
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

    const { data, isSuccess } = useGetRunningJobs({
        projectId: projectIdentifier.projectId,
        queryOptions: {
            enabled: isTraining,
            refetchIntervalInBackground: true,
            queryKey: QUERY_KEYS.JOBS_KEY(projectIdentifier, JobState.RUNNING, areTrainingDetails),
        },
    });

    useEffect(() => {
        if (!isSuccess) {
            return;
        }

        handleSuccess(data);
    }, [data, isSuccess, handleSuccess]);

    return data;
};

export const useTrainingProgress = (taskId: string): UseTrainingProgress => {
    const isTraining = useIsTraining();
    const data = useTrainingProgressJobs(isTraining);

    const getTrainingDetails = (): RunningTrainingJob | undefined => {
        const jobs = getAllJobs(data);
        const jobsPerTask = jobs.filter(
            (job) => isRunningTrainingJob(job) && taskId === job.metadata.task.taskId
        ) as RunningTrainingJob[];

        return !isEmpty(jobsPerTask) ? jobsPerTask[0] : undefined;
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
