// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useQueryClient } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { useJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { NORMAL_INTERVAL } from '../../../../../core/jobs/hooks/utils';
import { JobState, JobType } from '../../../../../core/jobs/jobs.const';
import { JobOptimization } from '../../../../../core/jobs/jobs.interface';
import { useModelIdentifier } from '../../../../../hooks/use-model-identifier/use-model-identifier.hook';

export const useIsModelBeingOptimized = (enabled: boolean): boolean => {
    const [isModelBeingOptimized, setIsModelBeingOptimized] = useState<boolean>(false);
    const queryClient = useQueryClient();

    const modelIdentifier = useModelIdentifier();
    const { useGetJobs } = useJobs(modelIdentifier);

    const { data } = useGetJobs(
        {
            jobTypes: [JobType.OPTIMIZATION_POT],
            projectId: modelIdentifier.projectId,
        },
        {
            enabled,
            refetchInterval: NORMAL_INTERVAL,
        }
    );

    useEffect(() => {
        if (!enabled) {
            return;
        }

        if (data === undefined) {
            return;
        }

        const jobs = data.pages.flatMap((page) => page.jobs) as JobOptimization[];
        const modelJobs = jobs.filter(
            (job) =>
                job.metadata.baseModelId === modelIdentifier.modelId &&
                job.metadata.modelStorageId === modelIdentifier.groupId
        );

        if (isEmpty(modelJobs)) {
            return;
        }

        const isRunningOrScheduledOptimizationJob = modelJobs.some((job) =>
            [JobState.RUNNING, JobState.SCHEDULED].includes(job.state)
        );

        const isFinishedOptimizationJob = !isRunningOrScheduledOptimizationJob;

        if (isRunningOrScheduledOptimizationJob && !isModelBeingOptimized) {
            setIsModelBeingOptimized(true);
        }

        if (isFinishedOptimizationJob && isModelBeingOptimized) {
            setIsModelBeingOptimized(false);

            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.MODEL_KEY(modelIdentifier) });
        }
    }, [data, isModelBeingOptimized, modelIdentifier, queryClient, enabled]);

    return isModelBeingOptimized;
};
