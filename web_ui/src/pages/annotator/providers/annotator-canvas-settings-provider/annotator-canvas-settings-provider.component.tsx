// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
