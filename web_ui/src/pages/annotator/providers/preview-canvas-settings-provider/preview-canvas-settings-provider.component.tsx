// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useState } from 'react';

import { noop } from 'lodash-es';

import { CANVAS_ADJUSTMENTS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { initialCanvasConfig } from '../../../../core/user-settings/utils';
import { UseCanvasSettings } from '../../hooks/use-canvas-settings.hook';
import { AnnotatorCanvasSettingsContext } from '../annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';

export const PreviewCanvasSettingsProvider = ({ children }: { children: ReactNode }) => {
    const [canvasConfig, setCanvasConfig] = useState(initialCanvasConfig);

    const handleCanvasSetting = (key: CANVAS_ADJUSTMENTS_KEYS, value: number | boolean): void => {
        setCanvasConfig((prevConfig) => ({
            ...prevConfig,
            [key]: {
                value,
                defaultValue: prevConfig[key].defaultValue,
            },
        }));
    };

    const canvasSettings: UseCanvasSettings = {
        canvasSettingsState: [canvasConfig, handleCanvasSetting],
        handleSaveConfig: noop,
    };

    return (
        <AnnotatorCanvasSettingsContext.Provider value={canvasSettings}>
            {children}
        </AnnotatorCanvasSettingsContext.Provider>
    );
};
