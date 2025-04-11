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

import { useEffect, useRef, useState } from 'react';

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
    loadImage: (imageData: ImageData) => void;
    isLoading: boolean;
    mutation: UseMutationResult<Shape | undefined, unknown, RITMData>;
    cancel: () => void;
}

export const useInteractiveSegmentation = ({
    showNotificationError,
    onSuccess,
}: useInteractiveSegmentationProps): useInteractiveSegmentationResult => {
    const { setIsDrawing } = useAnnotationScene();

    const { worker } = useLoadAIWebworker(AlgorithmType.RITM);

    const wsInstance = useRef<RITMMethods | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(true);
    const cancelRequested = useRef<boolean>(false);

    const cancel = () => {
        cancelRequested.current = true;
    };

    useEffect(() => {
        const loadWorker = async () => {
            if (worker) {
                wsInstance.current = await new worker.RITM();

                await wsInstance.current.load();

                setIsLoading(false);
            }
        };

        if (worker) {
            loadWorker();
        }

        return () => {
            if (wsInstance && wsInstance.current) {
                wsInstance.current.cleanMemory();
            }
        };
    }, [worker]);

    useEffect(() => {
        return () => setIsDrawing(false);
    }, [setIsDrawing]);

    const mutation = useMutation({
        mutationFn: ({ area, givenPoints, outputShape }: RITMData) => {
            if (!wsInstance.current) {
                throw 'Interactive segmentation not ready yet';
            }

            cancelRequested.current = false;
            setIsDrawing(true);

            return wsInstance.current.execute(area, givenPoints, outputShape);
        },

        onError: showNotificationError,

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

    const loadImage = (imageData: ImageData) => {
        if (!wsInstance.current) {
            console.warn('loading image before RITM is loaded...');

            return;
        }

        reset();
        wsInstance.current.loadImage(imageData);
    };

    return {
        cleanMask,
        reset,
        isLoading,
        loadImage,
        mutation,
        cancel,
    };
};
