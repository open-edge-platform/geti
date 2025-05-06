// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import {
    CreateApiModelConfigParametersService,
    TrainingConfigurationQueryParameters,
} from '../services/api-model-config-parameters-service';
import { TrainingConfigurationUpdatePayload } from '../services/configuration.interface';

const trainingConfigurationQueryOptions = (
    service: CreateApiModelConfigParametersService,
    projectIdentifier: ProjectIdentifier,
    queryParameters?: TrainingConfigurationQueryParameters
) =>
    queryOptions({
        queryKey: QUERY_KEYS.CONFIGURATION_PARAMETERS.TRAINING(projectIdentifier, queryParameters),
        queryFn: () => {
            return service.getTrainingConfiguration(projectIdentifier);
        },
    });

export const useTrainingConfigurationQuery = (
    projectIdentifier: ProjectIdentifier,
    queryParameters?: TrainingConfigurationQueryParameters
) => {
    const { configParametersService } = useApplicationServices();

    return useQuery(trainingConfigurationQueryOptions(configParametersService, projectIdentifier, queryParameters));
};

export const useTrainingConfigurationMutation = () => {
    const { configParametersService } = useApplicationServices();
    const queryClient = useQueryClient();

    return useMutation<
        void,
        AxiosError,
        {
            projectIdentifier: ProjectIdentifier;
            payload: TrainingConfigurationUpdatePayload;
            queryParameters?: TrainingConfigurationQueryParameters;
        }
    >({
        mutationFn: ({ projectIdentifier, payload, queryParameters }) => {
            return configParametersService.updateTrainingConfiguration(projectIdentifier, payload, queryParameters);
        },
        onSuccess: async (_, { projectIdentifier, queryParameters }) => {
            await queryClient.invalidateQueries({
                queryKey: QUERY_KEYS.CONFIGURATION_PARAMETERS.TRAINING(projectIdentifier, queryParameters),
            });
        },
    });
};
