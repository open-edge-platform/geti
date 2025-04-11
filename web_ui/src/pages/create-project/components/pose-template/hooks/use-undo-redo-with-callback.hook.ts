// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useRef } from 'react';

import { runWhen } from '../../../../../shared/utils';
import useUndoRedoState, { UseUndoRedoState } from '../../../../annotator/tools/undo-redo/use-undo-redo-state';
import { TemplateState } from '../util';

export const useUndoRedoWithCallback = (
    initialState: TemplateState,
    callback: (state: TemplateState) => void
): UseUndoRedoState<TemplateState> => {
    const isUndoRedo = useRef(false);
    const [state, setState, undoRedoActions] = useUndoRedoState(initialState);

    const onCanUndo = runWhen(() => undoRedoActions.canUndo);
    const onCanRedo = runWhen(() => undoRedoActions.canRedo);

    const enhancedUndoRedoActions = {
        ...undoRedoActions,
        undo: onCanUndo(() => {
            isUndoRedo.current = true;
            undoRedoActions.undo();
        }),
        redo: onCanRedo(() => {
            isUndoRedo.current = true;
            undoRedoActions.redo();
        }),
    };

    useEffect(() => {
        if (isUndoRedo.current === true) {
            callback(state);
            isUndoRedo.current = false;
        }
    }, [callback, state]);

    return [state, setState, enhancedUndoRedoActions];
};
