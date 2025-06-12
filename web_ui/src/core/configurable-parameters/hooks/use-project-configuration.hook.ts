// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { queryOptions, useMutation, useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import QUERY_KEYS from '../../../../packages/core/src/requests/query-keys';
import { ProjectIdentifier } from '../../projects/core.interface';
import {
    CreateApiModelConfigParametersService,
    ProjectConfigurationQueryParameters,
} from '../services/api-model-config-parameters-service';
import {
    ConfigurationParameter,
    KeyValueParameter,
    ProjectConfiguration,
    ProjectConfigurationUploadPayload,
} from '../services/configuration.interface';

type ProjectConfigurationQueryOptions = Pick<UseQueryOptions<ProjectConfiguration, AxiosError>, 'enabled'>;

const projectConfigurationQueryOptions = (
    service: CreateApiModelConfigParametersService,
    projectIdentifier: ProjectIdentifier,
    queryOptionsParams?: ProjectConfigurationQueryOptions
) =>
    queryOptions({
        queryKey: QUERY_KEYS.CONFIGURATION_PARAMETERS.PROJECT(projectIdentifier),
        queryFn: () => {
            return service.getProjectConfiguration(projectIdentifier);
        },
        ...queryOptionsParams,
    });

export const useProjectConfigurationQuery = (
    projectIdentifier: ProjectIdentifier,
    queryOptionsParams?: ProjectConfigurationQueryOptions
) => {
    const { configParametersService } = useApplicationServices();

    return useQuery(projectConfigurationQueryOptions(configParametersService, projectIdentifier, queryOptionsParams));
};

export const useProjectConfigurationMutation = () => {
    const { configParametersService } = useApplicationServices();
    const queryClient = useQueryClient();

    const getUpdatedParameters = (
        updatedParameter: KeyValueParameter[],
        previousParameters: ConfigurationParameter[]
    ): ConfigurationParameter[] => {
        return previousParameters.map((parameter) => {
            const updatedParam = updatedParameter.find((param) => param.key === parameter.key);
            if (updatedParam === undefined) {
                return parameter;
            }

            return {
                ...parameter,
                value: updatedParam.value,
            } as ConfigurationParameter;
        });
    };

    return useMutation<
        void,
        AxiosError,
        {
            projectIdentifier: ProjectIdentifier;
            payload: ProjectConfigurationUploadPayload;
            queryParameters?: ProjectConfigurationQueryParameters;
        },
        {
            previousConfiguration?: ProjectConfiguration;
        }
    >({
        mutationFn: ({ projectIdentifier, payload, queryParameters }) => {
            return configParametersService.updateProjectConfiguration(projectIdentifier, payload, queryParameters);
        },
        onMutate: async ({ projectIdentifier, payload, queryParameters }) => {
            const queryKey = projectConfigurationQueryOptions(configParametersService, projectIdentifier).queryKey;
            await queryClient.cancelQueries({
                queryKey,
            });

            const previousConfiguration = queryClient.getQueryData<ProjectConfiguration>(queryKey);

            if (previousConfiguration === undefined) {
                return {
                    previousConfiguration: undefined,
                };
            }

            queryClient.setQueryData<ProjectConfiguration>(queryKey, () => {
                const updatedConfiguration: ProjectConfiguration = {
                    taskConfigs: previousConfiguration.taskConfigs.map((taskConfig) => {
                        if (taskConfig.taskId === queryParameters?.taskId || queryParameters?.taskId === undefined) {
                            const payloadTaskConfig = payload.taskConfigs.find(
                                (config) => config.taskId === taskConfig.taskId
                            );

                            return {
                                ...taskConfig,
                                autoTraining:
                                    payloadTaskConfig?.autoTraining === undefined
                                        ? taskConfig.autoTraining
                                        : getUpdatedParameters(payloadTaskConfig.autoTraining, taskConfig.autoTraining),
                                training:
                                    payloadTaskConfig?.training === undefined
                                        ? taskConfig.training
                                        : {
                                              constraints: getUpdatedParameters(
                                                  payloadTaskConfig.training.constraints,
                                                  taskConfig.training.constraints
                                              ),
                                          },
                            };
                        }

                        return taskConfig;
                    }),
                };

                return updatedConfiguration;
            });

            return {
                previousConfiguration,
            };
        },
        onError: (_, { projectIdentifier }, context) => {
            if (context?.previousConfiguration == undefined) {
                return;
            }

            queryClient.setQueryData<ProjectConfiguration>(
                projectConfigurationQueryOptions(configParametersService, projectIdentifier).queryKey,
                () => context.previousConfiguration
            );
        },
        onSettled: async (_, __, { projectIdentifier }) => {
            await queryClient.invalidateQueries({
                queryKey: projectConfigurationQueryOptions(configParametersService, projectIdentifier).queryKey,
            });
        },
    });
};
