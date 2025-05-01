// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, useContext, useState } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { isKeypointTask } from '../../../../core/projects/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { StateProviderProps } from '../tools.interface';
import UndoRedoProvider from '../undo-redo/undo-redo-provider.component';
import useUndoRedoState, { SetStateWrapper } from '../undo-redo/use-undo-redo-state';
import { CursorDirection, getTemplateWithDirection } from './utils';

export interface KeypointStateContextProps {
    templateLabels: Label[];
    templatePoints: KeypointNode[];
    currentBoundingBox: RegionOfInterest | null;
    setCurrentBoundingBox: SetStateWrapper<RegionOfInterest | null>;
    setCursorDirection: (direction: CursorDirection) => void;
}

const KeypointStateContext = createContext<KeypointStateContextProps | undefined>(undefined);

export const KeypointStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const { project } = useProject();
    const [cursorDirection, setCursorDirection] = useState(CursorDirection.SouthEast);
    const [currentBoundingBox, setCurrentBoundingBox, undoRedoActions] = useUndoRedoState<RegionOfInterest | null>(
        null
    );

    const keypointTask = project.tasks.find(isKeypointTask);
    const templateLabels = keypointTask?.labels ?? [];
    const templatePoints = getTemplateWithDirection(keypointTask?.keypointStructure.positions ?? [], cursorDirection);

    return (
        <KeypointStateContext.Provider
            value={{ templateLabels, currentBoundingBox, templatePoints, setCurrentBoundingBox, setCursorDirection }}
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
