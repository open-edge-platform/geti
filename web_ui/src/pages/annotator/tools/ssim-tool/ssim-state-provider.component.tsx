// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

import { useMutation } from '@tanstack/react-query';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { isRotatedDetectionDomain } from '../../../../core/projects/domains';
import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { useLoadAIWebworker } from '../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { StateProviderProps } from '../tools.interface';
import UndoRedoProvider from '../undo-redo/undo-redo-provider.component';
import useUndoRedoState from '../undo-redo/use-undo-redo-state';
import { RunSSIMProps, SSIMMethods, SSIMState } from './ssim-tool.interface';
import { convertRectToShape, convertToRect, filterSSIMResults, guessNumberOfItemsThreshold } from './util';

export interface SSIMStateContextProps {
    reset: () => void;
    rerun: (props: Partial<RunSSIMProps>) => void;
    runSSIM: (props: RunSSIMProps) => void;
    toolState: SSIMState;
    updateToolState: (updatedProperties: Partial<SSIMState>, shapeType: ShapeType) => void;
    previewThreshold: number | null;
    setPreviewThreshold: (value: number | null) => void;
}

const initSSIMState: SSIMState = {
    shapes: [],
    matches: [],
    threshold: 0,
};

const SSIMStateContext = createContext<SSIMStateContextProps | undefined>(undefined);

export const SSIMStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const { worker } = useLoadAIWebworker(AlgorithmType.SSIM);

    const wsInstance = useRef<SSIMMethods | null>(null);

    const { activeDomains } = useTask();
    const { setIsDrawing } = useAnnotationScene();
    const [SSIMProps, setSSIMProps] = useState<RunSSIMProps | null>(null);
    const [toolState, setToolState, undoRedoActions] = useUndoRedoState<SSIMState>(initSSIMState);
    const [previewThreshold, setPreviewThreshold] = useState<number | null>(null);

    useEffect(() => {
        setPreviewThreshold(null);
    }, [toolState.threshold]);

    useEffect(() => {
        return () => setIsDrawing(false);
    }, [setIsDrawing]);

    const { mutate, reset: resetMutation } = useMutation({
        mutationFn: async (runSSIMProps: RunSSIMProps) => {
            setIsDrawing(true);

            if (!wsInstance.current && worker) {
                wsInstance.current = await new worker.SSIM();
            }

            if (wsInstance.current) {
                return wsInstance.current.executeSSIM(runSSIMProps);
            }

            return [];
        },

        onSuccess: (matches, { existingAnnotations, autoMergeDuplicates: merge, template, roi, shapeType }) => {
            const existingRects = merge ? existingAnnotations.map(convertToRect) : [];
            const absoluteTemplate = { ...template, x: template.x + roi.x, y: template.y + roi.y };
            const filteredMatches = filterSSIMResults(roi, matches, absoluteTemplate, existingRects);
            const threshold = guessNumberOfItemsThreshold(filteredMatches);

            updateToolState(
                {
                    matches: filteredMatches,
                    threshold,
                },
                shapeType
            );
        },
    });

    const rerun = (props: Partial<RunSSIMProps>) => {
        if (SSIMProps) {
            runSSIM({ ...SSIMProps, ...props });
        }
    };

    const runSSIM = (props: RunSSIMProps) => {
        setSSIMProps(props);
        mutate(props);
    };

    const reset = useCallback(async () => {
        undoRedoActions.reset(initSSIMState);
        resetMutation();
        setSSIMProps(null);
        setPreviewThreshold(null);
        wsInstance.current = null;
        setIsDrawing(false);
    }, [undoRedoActions, resetMutation, setIsDrawing]);

    const updateToolState = (updatedProperties: Partial<SSIMState>, shapeType: ShapeType) => {
        const newState = { ...toolState, ...updatedProperties };
        const matches = newState.matches.slice(0, newState.threshold);

        // Rotated detection projects do not support bounding boxes as annotations
        if (activeDomains.some(isRotatedDetectionDomain)) {
            shapeType = ShapeType.RotatedRect;
        }

        const shapes = matches.map(({ shape }) => convertRectToShape(shape, shapeType));

        setToolState({
            ...newState,
            shapes,
        });
    };

    return (
        <SSIMStateContext.Provider
            value={{
                reset,
                runSSIM,
                rerun,
                toolState,
                updateToolState,
                previewThreshold,
                setPreviewThreshold,
            }}
        >
            <UndoRedoProvider state={undoRedoActions}>{children}</UndoRedoProvider>
        </SSIMStateContext.Provider>
    );
};

export const useSSIMState = (): SSIMStateContextProps => {
    const context = useContext(SSIMStateContext);

    if (context === undefined) {
        throw new MissingProviderError('useSSIMState', 'SSIMStateProvider');
    }

    return context;
};
