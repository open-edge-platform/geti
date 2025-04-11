// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useCallback, useEffect, useRef } from 'react';

import { InfiniteData, useQueryClient } from '@tanstack/react-query';
import isEmpty from 'lodash/isEmpty';

import { useGetRunningJobs } from '../../../../../../core/jobs/hooks/use-jobs.hook';
import { JobState } from '../../../../../../core/jobs/jobs.const';
import { RunningTrainingJob } from '../../../../../../core/jobs/jobs.interface';
import { JobsResponse } from '../../../../../../core/jobs/services/jobs-service.interface';
import QUERY_KEYS from '../../../../../../core/requests/query-keys';
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
