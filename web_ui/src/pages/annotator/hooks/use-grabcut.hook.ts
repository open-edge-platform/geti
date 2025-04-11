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
