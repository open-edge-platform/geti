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

import { useMutation, useQueryClient, useSuspenseQuery } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { UserGlobalSettings, UseSettings } from '../services/user-settings.interface';
import { INITIAL_GLOBAL_SETTINGS } from '../utils';
import { SaveSettingsMutation, SaveSettingsMutationContext, SETTINGS_QUERY_STALE_TIME } from './utils';

const useQueryUserGlobalSettings = () => {
    const { userSettingsService } = useApplicationServices();

    const { data } = useSuspenseQuery<UserGlobalSettings, AxiosError>({
        queryKey: QUERY_KEYS.SETTINGS_KEY(),
        queryFn: () => {
            return userSettingsService.getGlobalSettings();
        },
        retry: false,
        staleTime: SETTINGS_QUERY_STALE_TIME,
    });

    return { data };
};

export const useUserGlobalSettings = (): UseSettings<UserGlobalSettings> => {
    const { userSettingsService } = useApplicationServices();
    const { addNotification } = useNotification();
    const queryClient = useQueryClient();

    const { data } = useQueryUserGlobalSettings();

    const settingsMutation = useMutation<
        void,
        AxiosError,
        SaveSettingsMutation<UserGlobalSettings>,
        SaveSettingsMutationContext<UserGlobalSettings>
    >({
        mutationFn: ({ settings }) => {
            return userSettingsService.saveGlobalSettings(settings);
        },

        onMutate: async ({ settings }) => {
            await queryClient.cancelQueries({ queryKey: QUERY_KEYS.SETTINGS_KEY() });

            const previousSettings = queryClient.getQueryData<UserGlobalSettings>(QUERY_KEYS.SETTINGS_KEY());

            queryClient.setQueryData<UserGlobalSettings>(QUERY_KEYS.SETTINGS_KEY(), () => settings);

            return {
                previousSettings,
            };
        },

        onSuccess: async (_data, variables) => {
            const { successMessage } = variables;
            successMessage && addNotification({ message: successMessage, type: NOTIFICATION_TYPE.INFO });
        },

        onError: (_, __, context) => {
            context?.previousSettings !== undefined &&
                queryClient.setQueryData<UserGlobalSettings>(QUERY_KEYS.SETTINGS_KEY(), () => context.previousSettings);

            addNotification({
                message: 'Failed to save settings. Please, try again later.',
                type: NOTIFICATION_TYPE.ERROR,
            });
        },

        onSettled: async () => {
            await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.SETTINGS_KEY() });
        },
    });

    const saveConfig = async (newSettingsConfig: UserGlobalSettings, successMessage?: string) => {
        return settingsMutation.mutateAsync({
            settings: newSettingsConfig,
            successMessage,
        });
    };

    return {
        config: data ?? INITIAL_GLOBAL_SETTINGS,
        saveConfig,
        isSavingConfig: settingsMutation.isPending,
    };
};
