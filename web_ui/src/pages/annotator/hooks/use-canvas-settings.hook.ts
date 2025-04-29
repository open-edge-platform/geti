// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
