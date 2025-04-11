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
