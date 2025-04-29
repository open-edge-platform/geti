// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { INITIAL_GLOBAL_SETTINGS, INITIAL_PROJECT_SETTINGS } from '../utils';
import { UserSettingsService } from './user-settings.interface';

export const createInMemoryUserSettingsService = (): UserSettingsService => {
    const getGlobalSettings: UserSettingsService['getGlobalSettings'] = async () => {
        return INITIAL_GLOBAL_SETTINGS;
    };

    const getProjectSettings: UserSettingsService['getProjectSettings'] = async () => {
        return INITIAL_PROJECT_SETTINGS;
    };

    const saveGlobalSettings: UserSettingsService['saveGlobalSettings'] = async () => {
        return Promise.resolve();
    };

    const saveProjectSettings: UserSettingsService['saveProjectSettings'] = async () => {
        return Promise.resolve();
    };

    return {
        getGlobalSettings,
        getProjectSettings,
        saveProjectSettings,
        saveGlobalSettings,
    };
};
