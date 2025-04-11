// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import isEmpty from 'lodash/isEmpty';

import { useJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { NORMAL_INTERVAL } from '../../../../../core/jobs/hooks/utils';
import { JobState, JobType } from '../../../../../core/jobs/jobs.const';
import { JobOptimization } from '../../../../../core/jobs/jobs.interface';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
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
