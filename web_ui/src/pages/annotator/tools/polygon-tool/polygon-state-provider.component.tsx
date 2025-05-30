// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, Dispatch, SetStateAction, useCallback, useContext, useState } from 'react';

import { Point } from '../../../../core/annotations/shapes.interface';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { UndoRedoActions } from '../../core/undo-redo-actions.interface';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { StateProviderProps } from '../tools.interface';
import UndoRedoProvider from '../undo-redo/undo-redo-provider.component';
import useUndoRedoState, { SetStateWrapper } from '../undo-redo/use-undo-redo-state';
import { PolygonMode } from './polygon-tool.enum';

export interface PolygonStateContextProps {
    segments: Point[][];
    mode: PolygonMode | null;
    isIntelligentScissorsLoaded: boolean;
    setSegments: SetStateWrapper<Point[][]>;
    undoRedoActions: UndoRedoActions<Point[][]>;
    setMode: (mode: PolygonMode | null) => void;
    setIsIntelligentScissorsLoaded: Dispatch<SetStateAction<boolean>>;
}

const PolygonStateContext = createContext<PolygonStateContextProps | undefined>(undefined);

export const PolygonStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const { getToolSettings, updateToolSettings } = useAnnotationToolContext();
    const { mode } = getToolSettings(ToolType.PolygonTool);
    const [segments, setSegments, undoRedoActions] = useUndoRedoState<Point[][]>([]);
    const [isIntelligentScissorsLoaded, setIsIntelligentScissorsLoaded] = useState<boolean>(false);

    const setMode = useCallback((inputMode: PolygonMode | null) => {
        updateToolSettings(ToolType.PolygonTool, { mode: inputMode });

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <PolygonStateContext.Provider
            value={{
                mode,
                setMode,
                segments,
                setSegments,
                undoRedoActions,
                isIntelligentScissorsLoaded,
                setIsIntelligentScissorsLoaded,
            }}
        >
            <UndoRedoProvider state={undoRedoActions}>{children}</UndoRedoProvider>
        </PolygonStateContext.Provider>
    );
};

export const usePolygonState = (): PolygonStateContextProps => {
    const context = useContext(PolygonStateContext);

    if (context === undefined) {
        throw new MissingProviderError('usePolygonState', 'PolygonStateProvider');
    }

    return context;
};
