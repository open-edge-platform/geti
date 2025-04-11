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

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import cloneDeep from 'lodash/cloneDeep';
import isNil from 'lodash/isNil';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import {
    ConfigurableParametersParams,
    ConfigurableParametersTaskChain,
} from '../../../shared/components/configurable-parameters/configurable-parameters.interface';
import {
    getReconfigureParametersDTO,
    updateSelectedParameter,
} from '../../../shared/components/configurable-parameters/utils';
import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';

interface UseReconfigureParams {
    configParameters: ConfigurableParametersTaskChain[];
    newConfigParameter: ConfigurableParametersParams;
    onOptimisticUpdate: (newConfig: ConfigurableParametersTaskChain[]) => ConfigurableParametersTaskChain[];
}

export const useReconfigAutoTraining = (projectIdentifier: ProjectIdentifier) => {
    const { configParametersService } = useApplicationServices();
    const { addNotification } = useNotification();
    const queryClient = useQueryClient();
    const configurationQueryKey = QUERY_KEYS.CONFIGURATION(projectIdentifier);

    return useMutation<void, AxiosError, UseReconfigureParams, ConfigurableParametersTaskChain[]>({
        mutationFn: async ({ configParameters, newConfigParameter }: UseReconfigureParams) => {
            return configParametersService.reconfigureParameters(
                projectIdentifier,
                getReconfigureParametersDTO(
                    updateSelectedParameter(
                        configParameters,
                        newConfigParameter.id,
                        newConfigParameter.id.split('::'),
                        newConfigParameter.value
                    )
                )
            );
        },

        onMutate: async ({ configParameters, onOptimisticUpdate }) => {
            await queryClient.cancelQueries({ queryKey: [configurationQueryKey] });

            const previousSnapshottedConfig = queryClient.getQueryData(
                configurationQueryKey
            ) as ConfigurableParametersTaskChain[];

            const newConfig = cloneDeep(configParameters);
            const updatedConfig = onOptimisticUpdate(newConfig);

            // Optimistically update to the new value
            queryClient.setQueryData(configurationQueryKey, updatedConfig);

            return previousSnapshottedConfig;
        },

        onError: (error, _variables, previousSnapshottedConfig) => {
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });

            if (!isNil(previousSnapshottedConfig)) {
                queryClient.setQueryData(configurationQueryKey, previousSnapshottedConfig);
            }
        },

        onSettled: (_data, error) => {
            if (!isNil(error)) {
                queryClient.invalidateQueries({ queryKey: [configurationQueryKey] });
            }
        },
    });
};
