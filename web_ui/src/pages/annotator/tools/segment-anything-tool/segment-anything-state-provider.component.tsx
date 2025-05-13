// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, useContext, useEffect } from 'react';

import { useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { Shape } from '../../../../core/annotations/shapes.interface';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAddUnfinishedShape } from '../../hooks/use-add-unfinished-shape.hook';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { StateProviderProps } from '../tools.interface';
import UndoRedoProvider from '../undo-redo/undo-redo-provider.component';
import useUndoRedoState from '../undo-redo/use-undo-redo-state';
import { useApplyLabelToPendingAnnotations } from '../useApplyLabelToPendingAnnotations';
import { EncodingOutput } from './model/segment-anything-encoder';
import { InteractiveAnnotationPoint } from './segment-anything.interface';
import { useDecodingMutation, useDecodingQuery, useDecodingQueryOptions } from './use-decoding-query.hook';
import { useSegmentAnythingModel } from './use-segment-anything-model.hook';
import { useSingleStackFn } from './use-single-stack-fn.hook';

interface SegmentAnythingState {
    points: InteractiveAnnotationPoint[];
}

interface SegmentAnythingStateContextProps {
    isProcessing: boolean;
    isLoading: boolean;

    points: InteractiveAnnotationPoint[];
    addPoint: (point: InteractiveAnnotationPoint, keepPreviousPoints?: boolean) => void;
    result: { shapes: Shape[] };
    handleCancelAnnotation: () => void;
    handleConfirmAnnotation: () => void;

    encodingQuery: UseQueryResult<EncodingOutput>;
    decodingQueryFn: (points: InteractiveAnnotationPoint[]) => Promise<Shape[]>;
}

const SegmentAnythingStateContext = createContext<SegmentAnythingStateContextProps | undefined>(undefined);

export const SegmentAnythingStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const [state, setState, undoRedoActions] = useUndoRedoState<SegmentAnythingState>({
        points: [],
    });

    const queryClient = useQueryClient();
    const { encodingQuery, decodingQueryFn, isLoading } = useSegmentAnythingModel();
    const throttledDecodingQueryFn = useSingleStackFn(decodingQueryFn);
    const decodingQueryOptions = useDecodingQueryOptions(state.points, throttledDecodingQueryFn);
    const decodingQuery = useDecodingQuery(state.points, throttledDecodingQueryFn);
    const { addNotification } = useNotification();
    useEffect(() => {
        if (state.points.length > 0 && decodingQuery.data !== undefined && decodingQuery.data.length === 0) {
            if (!decodingQuery.isPlaceholderData) {
                addNotification({
                    message: `Unable to segment object from the selected point${
                        state.points.length > 1 ? 's' : ''
                    }. Press ESC to reset points.`,
                    type: NOTIFICATION_TYPE.WARNING,
                });
            }
        }
    }, [decodingQuery.data, decodingQuery.isPlaceholderData, state.points, addNotification]);
    const decodingMutation = useDecodingMutation(decodingQueryFn);

    const { addShapes, setIsDrawing } = useAnnotationScene();

    const reset = async () => {
        queryClient.removeQueries({ queryKey: decodingQueryOptions.queryKey });
        undoRedoActions.reset({ points: [] });

        setIsDrawing(false);
    };

    useAddUnfinishedShape({
        shapes: state.points.length > 0 && decodingQuery.data ? decodingQuery.data : [],
        addShapes: (unfinishedShapes) => {
            reset();

            if (unfinishedShapes.length === 0) {
                return [];
            }

            const shapes = addShapes(unfinishedShapes as Shape[]);
            return shapes;
        },
        reset,
    });
    useEffect(() => {
        return () => setIsDrawing(false);
    }, [setIsDrawing]);

    const isProcessing = decodingQuery.isFetching;

    const hasResults = decodingQuery.data && !isEmpty(decodingQuery.data) && !isEmpty(state.points);
    const outputShapes = decodingQuery.data ?? [];
    const handleConfirmAnnotation = () => {
        if (isProcessing) {
            return;
        }

        if (hasResults) {
            addShapes(outputShapes);
        }

        reset();
    };

    const handleCancelAnnotation = () => {
        if (!isProcessing) {
            reset();
        }
    };

    const addPoint = (point: InteractiveAnnotationPoint, keepPreviousData = false) => {
        setIsDrawing(true);

        if (keepPreviousData) {
            setState((r) => ({ points: [...r.points, point] }));
        } else {
            undoRedoActions.reset({ points: [] });
            decodingMutation.mutateAsync([point]).then(() => {
                setIsDrawing(false);
            });
        }
    };

    const annotationToolContext = useAnnotationToolContext();
    useApplyLabelToPendingAnnotations({
        applyAnnotations: handleConfirmAnnotation,
        annotationToolContext,
        tool: ToolType.SegmentAnythingTool,
    });

    return (
        <SegmentAnythingStateContext.Provider
            value={{
                isProcessing,
                result: { shapes: outputShapes },
                isLoading,
                points: state.points,
                addPoint,
                handleConfirmAnnotation,
                handleCancelAnnotation,
                encodingQuery,
                decodingQueryFn,
            }}
        >
            <UndoRedoProvider state={undoRedoActions}>{children}</UndoRedoProvider>
        </SegmentAnythingStateContext.Provider>
    );
};

export const useSegmentAnything = (): SegmentAnythingStateContextProps => {
    const context = useContext(SegmentAnythingStateContext);

    if (context === undefined) {
        throw new MissingProviderError('useSegmentAnythingState', 'SegmentAnythingStateProvider');
    }

    return context;
};
