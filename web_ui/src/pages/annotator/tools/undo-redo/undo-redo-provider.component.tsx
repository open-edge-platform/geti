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

import { MissingProviderError } from '../../../../shared/missing-provider-error';
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
