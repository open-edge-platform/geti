// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useMutation, useQueryClient, useSuspenseQuery } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import QUERY_KEYS from '../../../../packages/core/src/requests/query-keys';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { ProjectIdentifier } from '../../projects/core.interface';
import { UserProjectSettings, UseSettings } from '../services/user-settings.interface';
import { INITIAL_PROJECT_SETTINGS } from '../utils';
import { SaveSettingsMutation, SaveSettingsMutationContext, SETTINGS_QUERY_STALE_TIME } from './utils';

const useQueryUserProjectSettings = (projectIdentifier: ProjectIdentifier) => {
    const { userSettingsService } = useApplicationServices();

    const { data } = useSuspenseQuery({
        queryKey: QUERY_KEYS.PROJECT_SETTINGS_KEY(projectIdentifier),
        queryFn: () => {
            return userSettingsService.getProjectSettings(projectIdentifier);
        },
        retry: false,
        staleTime: SETTINGS_QUERY_STALE_TIME,
    });

    return {
        data,
    };
};

export const useUserProjectSettings = (projectIdentifier: ProjectIdentifier): UseSettings<UserProjectSettings> => {
    const { userSettingsService } = useApplicationServices();
    const { addNotification } = useNotification();

    const queryClient = useQueryClient();

    const { data } = useQueryUserProjectSettings(projectIdentifier);

    const settingsMutation = useMutation<
        void,
        AxiosError,
        SaveSettingsMutation<UserProjectSettings>,
        SaveSettingsMutationContext<UserProjectSettings>
    >({
        mutationFn: ({ settings }) => {
            return userSettingsService.saveProjectSettings(projectIdentifier, settings);
        },

        onMutate: async ({ settings }) => {
            await queryClient.cancelQueries({
                queryKey: QUERY_KEYS.PROJECT_SETTINGS_KEY(projectIdentifier),
            });

            const previousSettings = queryClient.getQueryData<UserProjectSettings>(
                QUERY_KEYS.PROJECT_SETTINGS_KEY(projectIdentifier)
            );

            queryClient.setQueryData<UserProjectSettings>(
                QUERY_KEYS.PROJECT_SETTINGS_KEY(projectIdentifier),
                () => settings
            );

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
                queryClient.setQueryData<UserProjectSettings>(
                    QUERY_KEYS.PROJECT_SETTINGS_KEY(projectIdentifier),
                    () => context.previousSettings
                );

            addNotification({
                message: 'Failed to save settings. Please, try again later.',
                type: NOTIFICATION_TYPE.ERROR,
            });
        },

        onSettled: async () => {
            await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.PROJECT_SETTINGS_KEY(projectIdentifier) });
        },
    });

    const saveConfig = async (newSettingsConfig: UserProjectSettings, successMessage?: string) => {
        return settingsMutation.mutateAsync({
            settings: newSettingsConfig,
            successMessage,
        });
    };

    return {
        config: data ?? INITIAL_PROJECT_SETTINGS,
        saveConfig,
        isSavingConfig: settingsMutation.isPending,
    };
};
