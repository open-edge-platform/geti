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

import { useState } from 'react';

import isEqual from 'lodash/isEqual';

import {
    CANVAS_ADJUSTMENTS_KEYS,
    CanvasSettingsConfig,
} from '../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../core/user-settings/utils';

export type UseCanvasSettingsState = [
    canvasSettings: CanvasSettingsConfig,
    handleCanvasSetting: (key: CANVAS_ADJUSTMENTS_KEYS, value: number | boolean) => void,
];

export interface UseCanvasSettings {
    canvasSettingsState: UseCanvasSettingsState;
    handleSaveConfig: () => void;
}

export const useCanvasSettings = (settings: UseSettings<UserProjectSettings>): UseCanvasSettings => {
    const { config, saveConfig } = settings;
    const canvasSettingsConfig = getSettingsOfType(config, CANVAS_ADJUSTMENTS_KEYS) as CanvasSettingsConfig;
    const [canvasSettings, setCanvasSettings] = useState<CanvasSettingsConfig>(canvasSettingsConfig);

    const handleCanvasSetting = (key: CANVAS_ADJUSTMENTS_KEYS, value: number | boolean): void => {
        setCanvasSettings((prevSettings) => ({
            ...prevSettings,
            [key]: {
                value,
                defaultValue: prevSettings[key].defaultValue,
            },
        }));
    };

    const handleSaveConfig = (): void => {
        const newConfig = { ...config, ...canvasSettings };

        if (!isEqual(config, newConfig)) {
            saveConfig(newConfig);
        }
    };

    return {
        canvasSettingsState: [canvasSettings, handleCanvasSetting],
        handleSaveConfig,
    };
};
