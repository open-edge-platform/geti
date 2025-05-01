// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Label } from '../../../../core/labels/label.interface';
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
