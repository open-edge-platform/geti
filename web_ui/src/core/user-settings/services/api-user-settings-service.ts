// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { SettingsResponseDTO } from '../dtos/user-settings.interface';
import { INITIAL_GLOBAL_SETTINGS, INITIAL_PROJECT_SETTINGS } from '../utils';
import { UserGlobalSettings, UserSettingsService } from './user-settings.interface';

export const createApiUserSettingsService: CreateApiService<UserSettingsService> = (
    { instance, router } = { router: API_URLS, instance: apiClient }
) => {
    const getGlobalSettings: UserSettingsService['getGlobalSettings'] = async (): Promise<UserGlobalSettings> => {
        const { data } = await instance.get<SettingsResponseDTO>(router.GLOBAL_SETTINGS());

        try {
            const parsedSettings = JSON.parse(data.settings) ?? {};

            return {
                ...INITIAL_GLOBAL_SETTINGS,
                ...parsedSettings,
            };
        } catch {
            return INITIAL_GLOBAL_SETTINGS;
        }
    };

    const getProjectSettings: UserSettingsService['getProjectSettings'] = async (projectIdentifier) => {
        const { data } = await instance.get<SettingsResponseDTO>(router.PROJECT_SETTINGS(projectIdentifier));

        try {
            const settings = JSON.parse(data.settings) ?? {};

            return {
                ...INITIAL_PROJECT_SETTINGS,
                ...settings,
            };
        } catch {
            return INITIAL_PROJECT_SETTINGS;
        }
    };

    const saveGlobalSettings: UserSettingsService['saveGlobalSettings'] = async (settings) => {
        await instance.post(router.GLOBAL_SETTINGS(), { settings: JSON.stringify(settings) });
    };

    const saveProjectSettings: UserSettingsService['saveProjectSettings'] = async (projectIdentifier, settings) => {
        await instance.post(router.PROJECT_SETTINGS(projectIdentifier), { settings: JSON.stringify(settings) });
    };

    return {
        getProjectSettings,
        getGlobalSettings,
        saveGlobalSettings,
        saveProjectSettings,
    };
};
