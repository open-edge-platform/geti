// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { useMutation, UseMutationResult } from '@tanstack/react-query';

import { Shape } from '../../../core/annotations/shapes.interface';
import { AlgorithmType } from '../../../hooks/use-load-ai-webworker/algorithm.interface';
import { useLoadAIWebworker } from '../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';
import { useAnnotationScene } from '../providers/annotation-scene-provider/annotation-scene-provider.component';
import { RITMData, RITMMethods, RITMResult } from '../tools/ritm-tool/ritm-tool.interface';

interface useInteractiveSegmentationProps {
    onSuccess: (result: RITMResult) => void;
    showNotificationError: (error: unknown) => void;
}

interface useInteractiveSegmentationResult {
    cleanMask: () => void;
    reset: () => void;
    isLoading: boolean;
    mutation: UseMutationResult<Shape | undefined, unknown, RITMData>;
    cancel: () => void;
}

export const useInteractiveSegmentation = ({
    showNotificationError,
    onSuccess,
}: useInteractiveSegmentationProps): useInteractiveSegmentationResult => {
    const { setIsDrawing } = useAnnotationScene();
    const { worker, isLoading } = useLoadAIWebworker(AlgorithmType.RITM);

    const wsInstance = useRef<RITMMethods | null>(null);
    const cancelRequested = useRef<boolean>(false);

    const cancel = () => {
        cancelRequested.current = true;
    };

    useEffect(() => {
        return () => {
            if (wsInstance.current) {
                wsInstance.current.cleanMemory();
            }

            setIsDrawing(false);
        };

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const mutation = useMutation({
        mutationFn: async ({ imageData, area, givenPoints, outputShape }: RITMData) => {
            if (!worker) {
                throw 'Interactive segmentation worker not ready yet';
            }

            if (!wsInstance.current) {
                wsInstance.current = await worker.RITM(imageData);
            }

            cancelRequested.current = false;
            setIsDrawing(true);

            return wsInstance.current.execute(area, givenPoints, outputShape);
        },

        onError: (error) => {
            showNotificationError(error);
        },

        onSuccess: (shape, { givenPoints }: RITMData) => {
            if (cancelRequested.current) {
                return;
            }

            onSuccess({
                points: givenPoints,
                shape,
            });
        },
    });

    const cleanMask = () => {
        wsInstance?.current?.resetPointMask();
    };

    const reset = () => {
        setIsDrawing(false);
        wsInstance?.current?.reset();
    };

    return {
        cleanMask,
        reset,
        isLoading,
        mutation,
        cancel,
    };
};
