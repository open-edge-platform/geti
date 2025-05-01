// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersTaskChain } from '@shared/components/configurable-parameters/configurable-parameters.interface';
import { useMutation, UseMutationResult, useQuery, UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import { ConfigurableParametersReconfigureDTO } from '../dtos/configurable-parameters.interface';

interface UseConfigParameters {
    useGetConfigParameters: (isQueryEnabled: boolean) => UseQueryResult<ConfigurableParametersTaskChain[], AxiosError>;
    useGetModelConfigParameters: (
        args: {
            taskId: string;
            modelId?: string;
            modelTemplateId?: string | null;
            editable?: boolean;
        },
        options?: Pick<UseQueryOptions<ConfigurableParametersTaskChain, AxiosError>, 'enabled'>
    ) => UseQueryResult<ConfigurableParametersTaskChain, AxiosError>;
    reconfigureParametersMutation: UseMutationResult<void, AxiosError, ConfigurableParametersReconfigureDTO, unknown>;
}

export const useConfigParameters = (projectIdentifier: ProjectIdentifier): UseConfigParameters => {
    const { configParametersService } = useApplicationServices();

    const { addNotification } = useNotification();

    const useGetConfigParameters = (isQueryEnabled: boolean) =>
        useQuery<ConfigurableParametersTaskChain[], AxiosError>({
            queryKey: QUERY_KEYS.CONFIGURATION(projectIdentifier),
            queryFn: () => configParametersService.getConfigParameters(projectIdentifier),
            meta: { notifyOnError: true },
            enabled: isQueryEnabled,
        });

    const useGetModelConfigParameters: UseConfigParameters['useGetModelConfigParameters'] = (
        { taskId, modelId, modelTemplateId, editable },
        options
    ) =>
        useQuery<ConfigurableParametersTaskChain, AxiosError>({
            queryKey: QUERY_KEYS.MODEL_CONFIG_PARAMETERS(projectIdentifier, taskId, modelId, modelTemplateId),
            queryFn: () =>
                configParametersService.getModelConfigParameters(
                    projectIdentifier,
                    taskId,
                    modelId,
                    modelTemplateId,
                    editable
                ),
            meta: { notifyOnError: true },
            ...options,
        });

    const reconfigureParametersMutation = useMutation({
        mutationFn: (body: ConfigurableParametersReconfigureDTO) =>
            configParametersService.reconfigureParameters(projectIdentifier, body),

        onError: (error: AxiosError) => {
            addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
        },
    });

    return { useGetConfigParameters, useGetModelConfigParameters, reconfigureParametersMutation };
};
