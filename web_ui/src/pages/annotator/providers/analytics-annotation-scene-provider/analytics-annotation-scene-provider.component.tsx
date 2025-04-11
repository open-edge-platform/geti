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

import { MissingProviderError } from '../../../../shared/missing-provider-error';
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
