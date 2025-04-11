// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
