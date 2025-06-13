// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, Dispatch, SetStateAction, useCallback, useContext, useMemo, useRef, useState } from 'react';

import { type WatershedInstance, type WatershedPolygon } from '@geti/smart-tools';
import { UseMutateFunction, useMutation } from '@tanstack/react-query';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { useLoadAIWebworker } from '../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { UndoRedoActions } from '../../core/undo-redo-actions.interface';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { Marker } from '../marker-tool/marker-tool.interface';
import { StateProviderProps } from '../tools.interface';
import UndoRedoProvider from '../undo-redo/undo-redo-provider.component';
import useUndoRedoState, { SetStateWrapper } from '../undo-redo/use-undo-redo-state';
import { removeOffLimitPointsPolygon } from '../utils';
import { mapPolygonsToWatershedPolygons, WatershedPolygonWithLabel } from './utils';
import { RunWatershedProps } from './watershed-tool.interface';

interface WatershedState {
    markers: Marker[];
    watershedPolygons: WatershedPolygonWithLabel[];
}

interface WatershedStateContextProps {
    shapes: WatershedState;
    setShapes: SetStateWrapper<WatershedState>;
    watershedPolygons?: WatershedPolygon[];
    undoRedoActions: UndoRedoActions<WatershedState>;
    onComplete: (markers: Marker[]) => void;
    runWatershed: UseMutateFunction<WatershedPolygonWithLabel[], unknown, RunWatershedProps, unknown>;
    reset: () => Promise<void>;
    rejectAnnotation: () => Promise<void>;

    brushSize: number;
    setBrushSize: Dispatch<SetStateAction<number>>;

    isBrushSizePreviewVisible: boolean;
    setIsBrushSizePreviewVisible: Dispatch<SetStateAction<boolean>>;
}

const WatershedStateContext = createContext<WatershedStateContextProps | undefined>(undefined);

const DEFAULT_WATERSHED_STATE: WatershedState = {
    markers: [],
    watershedPolygons: [],
};

const useWatershedUndoRedoState = (): [
    WatershedState,
    SetStateWrapper<WatershedState>,
    UndoRedoActions<WatershedState>,
] => {
    const [shapes, setShapes, undoRedoActions] = useUndoRedoState<WatershedState>(DEFAULT_WATERSHED_STATE);

    const { roi } = useROI();

    // For each polygon produced by watershed we will remove any points that are outside
    // of the current ROI (selected input annotation in case of Task Chain)
    const shapesWithConstrainedPolygons = useMemo(() => {
        const polygons = shapes.watershedPolygons.map((watershedPolygon) => {
            const { points } = removeOffLimitPointsPolygon(
                { points: watershedPolygon.points, shapeType: ShapeType.Polygon },
                roi
            );

            return { ...watershedPolygon, points };
        });

        return {
            markers: shapes.markers,
            watershedPolygons: polygons,
        };
    }, [shapes, roi]);

    return [shapesWithConstrainedPolygons, setShapes, undoRedoActions];
};

export const WatershedStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const { worker } = useLoadAIWebworker(AlgorithmType.WATERSHED);

    const wsInstance = useRef<WatershedInstance | null>(null);

    const { addNotification } = useNotification();
    const { getToolSettings } = useAnnotationToolContext();
    const {
        project: { labels },
    } = useProject();

    const [shapes, setShapes, undoRedoActions] = useWatershedUndoRedoState();

    const watershedSettings = getToolSettings(ToolType.WatershedTool);

    const [brushSize, setBrushSize] = useState<number>(watershedSettings.brushSize);
    const [isBrushSizePreviewVisible, setIsBrushSizePreviewVisible] = useState<boolean>(false);

    const { mutate, reset: resetMutation } = useMutation({
        mutationFn: async (runWatershedProps: RunWatershedProps) => {
            let polygons: WatershedPolygon[] = [];
            if (worker && !wsInstance.current) {
                wsInstance.current = await worker.Watershed(runWatershedProps.imageData);
            }

            if (wsInstance.current) {
                polygons = await wsInstance.current.executeWatershed(
                    runWatershedProps.markers,
                    runWatershedProps.sensitivity
                );

                return mapPolygonsToWatershedPolygons(polygons, labels);
            }

            return [];
        },
        onError: () => {
            addNotification({
                message: 'Failed to run watershed algorithm, could you please try again?',
                type: NOTIFICATION_TYPE.ERROR,
            });
        },
    });

    const cleanUpWatershed = useCallback(async () => {
        resetMutation();

        // Clear instance memory and delete it afterwards
        if (wsInstance.current) {
            await wsInstance.current.clearMemory();

            wsInstance.current = null;
        }
    }, [resetMutation, wsInstance]);

    const reset = useCallback(async () => {
        undoRedoActions.reset();

        await cleanUpWatershed();
    }, [cleanUpWatershed, undoRedoActions]);

    const rejectAnnotation = useCallback(async () => {
        setShapes(DEFAULT_WATERSHED_STATE);

        await cleanUpWatershed();
    }, [cleanUpWatershed, setShapes]);

    const handleComplete = (newMarkers: Marker[]) => {
        setShapes(
            (previousShapes) => ({
                markers: [...previousShapes.markers, ...newMarkers],
                watershedPolygons: [...previousShapes.watershedPolygons],
            }),
            false
        );
    };

    return (
        <WatershedStateContext.Provider
            value={{
                shapes,
                setShapes,
                undoRedoActions,
                runWatershed: mutate,
                reset,
                rejectAnnotation,
                onComplete: handleComplete,

                brushSize,
                setBrushSize,

                isBrushSizePreviewVisible,
                setIsBrushSizePreviewVisible,
            }}
        >
            <UndoRedoProvider state={undoRedoActions}>{children}</UndoRedoProvider>
        </WatershedStateContext.Provider>
    );
};

export const useWatershedState = (): WatershedStateContextProps => {
    const context = useContext(WatershedStateContext);

    if (context === undefined) {
        throw new MissingProviderError('useWatershedState', 'WatershedStateProvider');
    }

    return context;
};
