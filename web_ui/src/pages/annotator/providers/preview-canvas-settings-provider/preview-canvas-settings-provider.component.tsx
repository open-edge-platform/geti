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

import { ReactNode, useState } from 'react';

import noop from 'lodash/noop';

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
