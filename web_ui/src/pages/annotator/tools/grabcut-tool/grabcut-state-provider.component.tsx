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

import { createContext, MutableRefObject, useCallback, useContext, useEffect, useRef } from 'react';

import { Point, Polygon, Rect } from '../../../../core/annotations/shapes.interface';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useGrabcut } from '../../hooks/use-grabcut.hook';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { StateProviderProps } from '../tools.interface';
import UndoRedoProvider from '../undo-redo/undo-redo-provider.component';
import useUndoRedoState, { SetStateWrapper } from '../undo-redo/use-undo-redo-state';
import { isPolygonValid } from '../utils';
import { GrabcutToolType } from './grabcut-tool.enums';

export interface GrabcutStateContextProps {
    isLoading: boolean;
    toolsState: GrabcutState;
    loadingRect: MutableRefObject<Rect | null>;
    foregroundMarkers: MutableRefObject<Point[][]>;
    backgroundMarkers: MutableRefObject<Point[][]>;
    resetConfig: () => void;
    rejectAnnotation: () => void;
    setDrawingToFalse: () => void;
    setToolsState: SetStateWrapper<GrabcutState>;
    runGrabcut: (image: ImageData, strokeWidth: number, sensitivity: number) => void;
}

const GrabcutStateContext = createContext<GrabcutStateContextProps | undefined>(undefined);

export interface GrabcutState {
    polygon: Polygon | null;
    inputRect: Rect | null;
    background: Point[][];
    foreground: Point[][];
    activeTool: GrabcutToolType;
}

const initialState: GrabcutState = {
    polygon: null,
    foreground: [],
    background: [],
    inputRect: null,
    activeTool: GrabcutToolType.InputTool,
};

export const GrabcutStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const loadingRect = useRef<Rect | null>(null);
    const { setIsDrawing } = useAnnotationScene();
    const { addNotification } = useNotification();
    const foregroundMarkers = useRef<Point[][]>([]);
    const backgroundMarkers = useRef<Point[][]>([]);
    const [toolsState, setToolsState, undoRedoActions] = useUndoRedoState<GrabcutState>(initialState);
    const { updateToolSettings } = useAnnotationToolContext();

    const showNotificationError = () => {
        addNotification({
            message: 'Failed to select the shape boundaries, could you please try again?',
            type: NOTIFICATION_TYPE.ERROR,
        });
        resetConfig();
    };

    const { mutation, cleanModels, isLoadingGrabcut } = useGrabcut({
        showNotificationError,
        onSuccess: ({ shapeType, points }, { foreground, background, sensitivity, ...variables }) => {
            const polygon = { shapeType, points };

            if (isPolygonValid(polygon)) {
                setToolsState((prev) => ({
                    ...prev,
                    foreground: [...foreground],
                    background: [...background],
                    inputRect: variables.inputRect,
                    polygon,
                }));

                updateToolSettings(ToolType.GrabcutTool, { sensitivity });
            } else {
                resetConfig();
            }
        },
    });

    useEffect(() => {
        return () => setIsDrawing(false);
    }, [setIsDrawing]);

    useEffect(() => {
        if (mutation.isPending) {
            return;
        }

        foregroundMarkers.current = [...toolsState.foreground];
        backgroundMarkers.current = [...toolsState.background];
        loadingRect.current = toolsState.inputRect;

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [toolsState.foreground, toolsState.background, toolsState.inputRect]);

    const runGrabcut = (imageData: ImageData, strokeWidth: number, sensitivity: number): void => {
        if (loadingRect.current) {
            setIsDrawing(true);

            mutation.mutate({
                image: imageData,
                strokeWidth,
                sensitivity,
                inputRect: loadingRect.current,
                activeTool: toolsState.activeTool,
                foreground: foregroundMarkers.current,
                background: backgroundMarkers.current,
            });
        }
    };

    const cleanUpGrabcut = useCallback(
        () => {
            cleanModels();

            loadingRect.current = null;
            foregroundMarkers.current = [];
            backgroundMarkers.current = [];

            setIsDrawing(false);
        },

        // eslint-disable-next-line react-hooks/exhaustive-deps
        []
    );

    const setDrawingToFalse = () => setIsDrawing(false);

    const resetConfig = useCallback((): void => {
        cleanUpGrabcut();
        undoRedoActions.reset(initialState);
    }, [cleanUpGrabcut, undoRedoActions]);

    const rejectAnnotation = useCallback(() => {
        cleanUpGrabcut();
        setToolsState(initialState);
    }, [cleanUpGrabcut, setToolsState]);

    return (
        <GrabcutStateContext.Provider
            value={{
                toolsState,
                loadingRect,
                foregroundMarkers,
                backgroundMarkers,
                runGrabcut,
                resetConfig,
                setToolsState,
                rejectAnnotation,
                setDrawingToFalse,
                isLoading: isLoadingGrabcut || mutation.isPending,
            }}
        >
            <UndoRedoProvider state={undoRedoActions}>{children}</UndoRedoProvider>
        </GrabcutStateContext.Provider>
    );
};

export const useGrabcutState = (): GrabcutStateContextProps => {
    const context = useContext(GrabcutStateContext);

    if (context === undefined) {
        throw new MissingProviderError('useGrabcutState', 'GrabcutStateProvider');
    }

    return context;
};
