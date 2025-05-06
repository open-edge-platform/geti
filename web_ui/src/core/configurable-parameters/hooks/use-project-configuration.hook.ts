// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import {
    CreateApiModelConfigParametersService,
    ProjectConfigurationQueryParameters,
} from '../services/api-model-config-parameters-service';
import { ProjectConfigurationUploadPayload } from '../services/configuration.interface';

const projectConfigurationQueryOptions = (
    service: CreateApiModelConfigParametersService,
    projectIdentifier: ProjectIdentifier
) =>
    queryOptions({
        queryKey: QUERY_KEYS.CONFIGURATION_PARAMETERS.PROJECT(projectIdentifier),
        queryFn: () => {
            return service.getProjectConfiguration(projectIdentifier);
        },
    });

export const useProjectConfigurationQuery = (projectIdentifier: ProjectIdentifier) => {
    const { configParametersService } = useApplicationServices();

    return useQuery(projectConfigurationQueryOptions(configParametersService, projectIdentifier));
};

export const useProjectConfigurationMutation = () => {
    const { configParametersService } = useApplicationServices();
    const queryClient = useQueryClient();

    return useMutation<
        void,
        AxiosError,
        {
            projectIdentifier: ProjectIdentifier;
            payload: ProjectConfigurationUploadPayload;
            queryParameters?: ProjectConfigurationQueryParameters;
        }
    >({
        mutationFn: ({ projectIdentifier, payload, queryParameters }) => {
            return configParametersService.updateProjectConfiguration(projectIdentifier, payload, queryParameters);
        },
        onSuccess: async (_, { projectIdentifier }) => {
            await queryClient.invalidateQueries({
                queryKey: projectConfigurationQueryOptions(configParametersService, projectIdentifier).queryKey,
            });
        },
    });
};
