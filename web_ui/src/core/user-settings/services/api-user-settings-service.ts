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

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { SettingsResponseDTO } from '../dtos/user-settings.interface';
import { INITIAL_GLOBAL_SETTINGS, INITIAL_PROJECT_SETTINGS } from '../utils';
import { UserGlobalSettings, UserSettingsService } from './user-settings.interface';

export const createApiUserSettingsService: CreateApiService<UserSettingsService> = (
    { instance, router } = { router: API_URLS, instance: defaultAxiosInstance }
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
