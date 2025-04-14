// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { Remote } from 'comlink';

import { Polygon } from '../../../core/annotations/shapes.interface';
import { AlgorithmType } from '../../../hooks/use-load-ai-webworker/algorithm.interface';
import { useLoadAIWebworker } from '../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';
import { GrabcutData, GrabcutMethods } from '../tools/grabcut-tool/grabcut-tool.interface';

interface useGrabcutProps {
    onSuccess: (data: Polygon, variables: GrabcutData) => void;
    showNotificationError: (error: unknown) => void;
}

interface useGrabcutResult {
    cleanModels: () => void;
    isLoadingGrabcut: boolean;
    mutation: UseMutationResult<Polygon, unknown, GrabcutData>;
}

export const useGrabcut = ({ showNotificationError, onSuccess }: useGrabcutProps): useGrabcutResult => {
    const { worker, isLoading } = useLoadAIWebworker(AlgorithmType.GRABCUT);
    const grabcutRef = useRef<Remote<GrabcutMethods> | null>(null);

    useEffect(() => {
        return () => {
            cleanModels();
        };
    }, [worker]);

    const mutation = useMutation({
        mutationFn: async ({ image, ...data }: GrabcutData) => {
            if (worker) {
                const instance = await new worker.Grabcut(image);

                grabcutRef.current = instance;

                return instance.startGrabcut(data);
            } else {
                return Promise.reject();
            }
        },

        onError: showNotificationError,

        onSuccess: (data: Polygon, variables: GrabcutData) => {
            onSuccess(data, variables);
        },
    });

    const cleanModels = () => {
        if (grabcutRef.current) {
            grabcutRef.current.cleanModels();
        }

        grabcutRef.current = null;
    };

    return { mutation, isLoadingGrabcut: isLoading, cleanModels };
};
