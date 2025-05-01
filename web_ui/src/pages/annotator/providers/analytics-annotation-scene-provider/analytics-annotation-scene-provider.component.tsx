// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';

import { ToolType } from '../../core/annotation-tool-context.interface';
import {
    AnnotationSceneContext,
    useAnnotationScene,
} from '../annotation-scene-provider/annotation-scene-provider.component';
import {
    ToolPerAnnotationState,
    useEnhancedAnalyticsAnnotationScene,
} from './use-enhanced-analytics-annotation-scene.hook';

const AnalyticsAnnotationToolsContext = createContext<undefined | ToolPerAnnotationState>(undefined);

interface AnalyticsAnnotationSceneProviderProps {
    children: ReactNode;
    activeTool: ToolType;
}

export const AnalyticsAnnotationSceneProvider = ({
    children,
    activeTool,
}: AnalyticsAnnotationSceneProviderProps): JSX.Element => {
    const parentScene = useAnnotationScene();
    const [scene, toolPerAnnotationState] = useEnhancedAnalyticsAnnotationScene(parentScene, activeTool);

    return (
        <AnnotationSceneContext.Provider value={scene}>
            <AnalyticsAnnotationToolsContext.Provider value={toolPerAnnotationState}>
                {children}
            </AnalyticsAnnotationToolsContext.Provider>
        </AnnotationSceneContext.Provider>
    );
};

export const useAnalyticsAnnotationTools = (): ToolPerAnnotationState => {
    const context = useContext(AnalyticsAnnotationToolsContext);

    if (context == undefined) {
        throw new MissingProviderError('useAnalyticsAnnotationTools', 'AnalyticsAnnotationSceneProvider');
    }

    return context;
};
