// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, ReactNode, useContext } from 'react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Label } from '../../../../core/labels/label.interface';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import UndoRedoProvider from '../../tools/undo-redo/undo-redo-provider.component';
import { useAnnotationSceneState } from './use-annotation-scene-state.hook';

export const AnnotationSceneContext = createContext<AnnotationScene | undefined>(undefined);

interface AnnotationsProviderProps {
    readonly annotations: ReadonlyArray<Annotation>;
    readonly labels: ReadonlyArray<Label>;
    activeUserId?: string | undefined;
    children: ReactNode;
}

export const AnnotationSceneProvider = ({
    labels,
    children,
    annotations: initialAnnotations,
    activeUserId,
}: AnnotationsProviderProps): JSX.Element => {
    const { undoRedoActions, ...annotationScene } = useAnnotationSceneState(initialAnnotations, labels, activeUserId);

    return (
        <AnnotationSceneContext.Provider value={annotationScene}>
            <UndoRedoProvider state={undoRedoActions}>{children}</UndoRedoProvider>
        </AnnotationSceneContext.Provider>
    );
};

export const useAnnotationScene = (): AnnotationScene => {
    const context = useContext(AnnotationSceneContext);

    if (context === undefined) {
        throw new MissingProviderError('useAnnotationScene', 'AnnotationSceneProvider');
    }

    return context;
};
