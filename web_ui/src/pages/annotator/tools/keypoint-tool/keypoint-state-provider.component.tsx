// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, useContext } from 'react';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { isKeypointTask } from '../../../../core/projects/utils';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { StateProviderProps } from '../tools.interface';
import UndoRedoProvider from '../undo-redo/undo-redo-provider.component';
import useUndoRedoState, { SetStateWrapper } from '../undo-redo/use-undo-redo-state';

export interface KeypointStateContextProps {
    templateLabels: Label[];
    templatePoints: KeypointNode[];
    currentBoundingBox: RegionOfInterest | null;
    setCurrentBoundingBox: SetStateWrapper<RegionOfInterest | null>;
}

const KeypointStateContext = createContext<KeypointStateContextProps | undefined>(undefined);

export const KeypointStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const { project } = useProject();
    const [currentBoundingBox, setCurrentBoundingBox, undoRedoActions] = useUndoRedoState<RegionOfInterest | null>(
        null
    );

    const keypointTask = project.tasks.find(isKeypointTask);
    const templatePoints = keypointTask?.keypointStructure.positions ?? [];
    const templateLabels = keypointTask?.labels ?? [];

    return (
        <KeypointStateContext.Provider
            value={{ templateLabels, currentBoundingBox, templatePoints, setCurrentBoundingBox }}
        >
            <UndoRedoProvider state={undoRedoActions}>{children}</UndoRedoProvider>
        </KeypointStateContext.Provider>
    );
};

export const useKeypointState = (): KeypointStateContextProps => {
    const context = useContext(KeypointStateContext);

    if (context === undefined) {
        throw new MissingProviderError('useKeypointState', 'KeypointStateProvider');
    }

    return context;
};
