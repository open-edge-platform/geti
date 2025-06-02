// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { InferenceServerStatusResult } from '../../../../core/annotations/services/prediction-service.interface';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
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
