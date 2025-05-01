// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';

import { UndoRedoActions } from '../../core/undo-redo-actions.interface';

const UndoRedoContext = createContext<UndoRedoActions | undefined>(undefined);

interface UndoRedoProviderProps {
    children: ReactNode;
    state: UndoRedoActions;
}

const UndoRedoProvider = ({ state, children }: UndoRedoProviderProps): JSX.Element => {
    return <UndoRedoContext.Provider value={state}>{children}</UndoRedoContext.Provider>;
};

export const useParentUndoRedo = (): UndoRedoActions | undefined => {
    return useContext(UndoRedoContext);
};

export const useUndoRedo = (): UndoRedoActions => {
    const context = useParentUndoRedo();

    if (context === undefined) {
        throw new MissingProviderError('useUndoRedo', 'UndoRedoProvider');
    }

    return context;
};

export default UndoRedoProvider;
