// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { InferenceServerStatusResult } from '../../../../core/annotations/services/prediction-service.interface';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';
import { useTask } from '../task-provider/task-provider.component';

export const useInferenceServerStatus = (
    projectIdentifier: ProjectIdentifier,
    enabled = true
): UseQueryResult<InferenceServerStatusResult, AxiosError> => {
    const { selectedTask, tasks } = useTask();
    const { inferenceService } = useApplicationServices();

    const taskId = tasks.length > 1 ? selectedTask?.id : undefined;

    return useQuery<InferenceServerStatusResult, AxiosError>({
        enabled,
        queryKey: QUERY_KEYS.INFERENCE_SERVER_KEY(projectIdentifier),
        queryFn: () => inferenceService.getInferenceServerStatus(projectIdentifier, taskId),
        meta: { notifyOnError: true },
        refetchInterval: (query) => {
            return query?.state?.data?.isInferenceServerReady ? 60_000 : 10_000;
        },
        notifyOnChangeProps: ['data'],
    });
};
