// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
