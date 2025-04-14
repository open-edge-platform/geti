// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    UserGlobalSettings,
    UserProjectSettings,
    UseSettings,
} from '../../core/user-settings/services/user-settings.interface';
import { INITIAL_GLOBAL_SETTINGS, INITIAL_PROJECT_SETTINGS } from '../../core/user-settings/utils';

export const getMockedUserGlobalSettings = (settings: Partial<UserGlobalSettings> = {}) => ({
    ...INITIAL_GLOBAL_SETTINGS,
    ...settings,
});

export const getMockedUserProjectSettings = (settings: Partial<UserProjectSettings> = {}) => ({
    ...INITIAL_PROJECT_SETTINGS,
    ...settings,
});

export const getMockedUserGlobalSettingsObject = (
    options: Partial<UseSettings<UserGlobalSettings>> = {}
): UseSettings<UserGlobalSettings> => {
    const { config, ...settings } = options;

    return {
        saveConfig: jest.fn(),
        isSavingConfig: false,
        config: getMockedUserGlobalSettings(config),
        ...settings,
    };
};

export const getMockedUserProjectSettingsObject = (
    options: Partial<UseSettings<UserProjectSettings>> = {}
): UseSettings<UserProjectSettings> => {
    const { config, ...settings } = options;

    return {
        saveConfig: jest.fn(),
        isSavingConfig: false,
        config: getMockedUserProjectSettings(config),
        ...settings,
    };
};
