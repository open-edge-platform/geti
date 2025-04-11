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

import { useMutation, UseMutationResult, useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query/src/types';
import { AxiosError } from 'axios';
import isEmpty from 'lodash/isEmpty';

import { useProjectIdentifier } from '../../../hooks/use-project-identifier/use-project-identifier';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { useTasksWithSupportedAlgorithms } from '../../../pages/project-details/hooks/use-tasks-with-supported-algorithms';
import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import { TrainingBodyDTO } from '../dtos/train-model.interface';
import { ModelGroupIdentifier, ModelIdentifier, ModelsGroups } from '../models.interface';
import { ModelDetails } from '../optimized-models.interface';
import { hasActiveModels } from '../utils';

interface UseModels {
    useModelQuery: (modelIdentifier: ModelIdentifier) => UseQueryResult<ModelDetails, AxiosError>;

    useModelsGroupQuery: (modelGroupIdentifier: ModelGroupIdentifier) => UseQueryResult<ModelsGroups, AxiosError>;

    useModelsQuery: (projectIdentifier: ProjectIdentifier) => UseQueryResult<ModelsGroups[], AxiosError>;
    useTrainModelMutation: () => UseMutationResult<void, AxiosError, UseTrainModelMutation>;
    useOptimizeModelMutation: () => UseMutationResult<void, AxiosError, UseOptimizeModelMutation>;
    useActivateModelMutation: () => UseMutationResult<void, AxiosError, ModelGroupIdentifier>;
    useProjectModelsQuery: (
        queryOptions?: Pick<UseQueryOptions<ModelsGroups[], AxiosError, ModelsGroups[]>, 'refetchInterval'>
    ) => ReturnType<UseModels['useModelsQuery']>;
    useProjectModelQuery: (groupId: string, modelId: string) => ReturnType<UseModels['useModelQuery']>;
    useHasActiveModels: () => { hasActiveModels: boolean; isSuccess: boolean };
    useArchiveModelMutation: () => UseMutationResult<void, AxiosError, ModelIdentifier, unknown>;
}

interface UseOptimizeModelMutation {
    modelIdentifier: ModelIdentifier;
}

interface UseTrainModelMutation {
    projectIdentifier: ProjectIdentifier;
    body: TrainingBodyDTO;
}

export const useModels = (): UseModels => {
    const { modelsService } = useApplicationServices();
    const { addNotification } = useNotification();

    const onError = (error: AxiosError) => {
        addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
    };

    const useModelQuery = (modelIdentifier: ModelIdentifier): UseQueryResult<ModelDetails, AxiosError> => {
        const { groupId, modelId } = modelIdentifier;
        const isQueryEnabled = groupId && modelId;

        return useQuery<ModelDetails, AxiosError>({
            queryKey: QUERY_KEYS.MODEL_KEY(modelIdentifier),
            queryFn: () => modelsService.getModel(modelIdentifier),
            meta: { notifyOnError: true },
            enabled: !!isQueryEnabled,
        });
    };

    const useModelsQuery = (
        projectIdentifier: ProjectIdentifier,
        queryOptions?: Pick<UseQueryOptions<ModelsGroups[], AxiosError, ModelsGroups[]>, 'refetchInterval'>
    ): UseQueryResult<ModelsGroups[], AxiosError> => {
        const { tasksWithSupportedAlgorithms } = useTasksWithSupportedAlgorithms();

        return useQuery<ModelsGroups[], AxiosError>({
            queryKey: QUERY_KEYS.MODELS_KEY(projectIdentifier),
            queryFn: () => modelsService.getModels(projectIdentifier, tasksWithSupportedAlgorithms),
            meta: { notifyOnError: true },
            enabled: !isEmpty(tasksWithSupportedAlgorithms),
            ...queryOptions,
        });
    };

    const useProjectModelsQuery: UseModels['useProjectModelsQuery'] = (
        queryOptions
    ): UseQueryResult<ModelsGroups[], AxiosError> => {
        const projectIdentifier = useProjectIdentifier();

        return useModelsQuery(projectIdentifier, queryOptions);
    };

    const useProjectModelQuery = (groupId: string, modelId: string): UseQueryResult<ModelDetails, AxiosError> => {
        const projectIdentifier = useProjectIdentifier();

        return useModelQuery({ ...projectIdentifier, groupId, modelId });
    };

    const useModelsGroupQuery = (
        modelGroupIdentifier: ModelGroupIdentifier
    ): UseQueryResult<ModelsGroups, AxiosError> => {
        const { tasksWithSupportedAlgorithms } = useTasksWithSupportedAlgorithms();

        return useQuery<ModelsGroups, AxiosError>({
            queryKey: QUERY_KEYS.MODELS_GROUP(modelGroupIdentifier),
            queryFn: () => modelsService.getModelsByArchitecture(modelGroupIdentifier, tasksWithSupportedAlgorithms),
            meta: { notifyOnError: true },
            enabled: !isEmpty(tasksWithSupportedAlgorithms),
        });
    };

    const useOptimizeModelMutation = (): UseMutationResult<void, AxiosError, UseOptimizeModelMutation> => {
        return useMutation<void, AxiosError, UseOptimizeModelMutation>({
            mutationFn: ({ modelIdentifier }: UseOptimizeModelMutation) => modelsService.optimizeModel(modelIdentifier),
            onError,
        });
    };

    const useTrainModelMutation = (): UseMutationResult<void, AxiosError, UseTrainModelMutation> => {
        return useMutation({
            mutationFn: ({ projectIdentifier, body }: UseTrainModelMutation) =>
                modelsService.trainModel(projectIdentifier, body),
            onError,
        });
    };

    const useActivateModelMutation = (): UseMutationResult<void, AxiosError, ModelGroupIdentifier> => {
        const queryClient = useQueryClient();

        return useMutation<void, AxiosError, ModelGroupIdentifier>({
            mutationFn: modelsService.activateModel,
            onError,
            onSuccess: async (_, { ...projectIdentifier }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.MODELS_KEY(projectIdentifier) });
            },
        });
    };

    const useHasActiveModels = () => {
        const { data: modelsData = [], isSuccess } = useProjectModelsQuery({
            // If we detect that we don't have any active models yet we will poll the server
            // as it might be possible that a training job has started
            // This makes sure that the UI will start getting inference results once we do
            // have an active model
            refetchInterval: (query) => {
                const data = query.state.data;
                if (data === undefined || !data.some(hasActiveModels)) {
                    return 60_000;
                }

                return false;
            },
        });

        return { hasActiveModels: modelsData.some(hasActiveModels), isSuccess };
    };

    const useArchiveModelMutation = () => {
        const queryClient = useQueryClient();

        return useMutation<void, AxiosError, ModelIdentifier>({
            mutationFn: modelsService.archiveModel,
            onError,
            onSuccess: async (_, { ...projectIdentifier }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.MODELS_KEY(projectIdentifier) });
            },
        });
    };

    return {
        useModelQuery,
        useModelsQuery,
        useModelsGroupQuery,
        useTrainModelMutation,
        useOptimizeModelMutation,
        useActivateModelMutation,
        useProjectModelsQuery,
        useProjectModelQuery,
        useHasActiveModels,
        useArchiveModelMutation,
    };
};
