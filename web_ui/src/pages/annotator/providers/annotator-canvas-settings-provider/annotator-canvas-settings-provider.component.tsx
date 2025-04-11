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

import { createContext, ReactNode, useContext } from 'react';

import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { UseCanvasSettings, useCanvasSettings } from '../../hooks/use-canvas-settings.hook';

interface AnnotatorCanvasSettingsProviderProps {
    children: ReactNode;
    settings: UseSettings<UserProjectSettings>;
}

export const AnnotatorCanvasSettingsContext = createContext<UseCanvasSettings | undefined>(undefined);

export const AnnotatorCanvasSettingsProvider = ({ children, settings }: AnnotatorCanvasSettingsProviderProps) => {
    const canvasSettings = useCanvasSettings(settings);

    return (
        <AnnotatorCanvasSettingsContext.Provider value={canvasSettings}>
            {children}
        </AnnotatorCanvasSettingsContext.Provider>
    );
};

export const useAnnotatorCanvasSettings = (): UseCanvasSettings => {
    const context = useContext(AnnotatorCanvasSettingsContext);

    if (context === undefined) {
        throw new MissingProviderError('useAnnotatorCanvasSettings', 'AnnotatorCanvasSettingsProvider');
    }

    return context;
};
