// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useMemo, useRef, useState } from 'react';

import { i18n } from '@/i18n';
import { roiFromImage } from '@geti-ui/smart-tools/utils';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { Remote } from 'comlink';
import { clamp } from 'lodash-es';

import type { Shape } from '../../../../shared/types';
import { executeWithTimeout } from '../../smart-tools/execute-with-timeout';
import { SSIM_WORKER_QUERY_KEY, useSSIMWorker } from '../../smart-tools/use-ssim-worker.hook';
import type { SSIMWorkerInstance } from '../../smart-tools/webworkers/ssim-worker.interface';
import {
    convertRectToShape,
    convertToolMatchesToGetiMatches,
    filterSSIMResults,
    getExistingRects,
    guessNumberOfItemsThreshold,
    toToolRunSSIMProps,
    type RunSSIMProps,
    type SSIMMatch,
    type SSIMShapeType,
} from './utils';

const SSIM_EXECUTE_TIMEOUT_MS = 10_000;

type SSIMState = {
    shapes: Shape[];
    matches: SSIMMatch[];
    threshold: number;
};

const INITIAL_SSIM_STATE: SSIMState = {
    shapes: [],
    matches: [],
    threshold: 0,
};

type SSIMRun = {
    props: RunSSIMProps;
    runId: number;
    keepNumberOfItems: boolean;
};

const withShapes = (state: Omit<SSIMState, 'shapes'>, shapeType: SSIMShapeType): SSIMState => ({
    ...state,
    shapes: state.matches.slice(0, state.threshold).map(({ shape }) => convertRectToShape(shape, shapeType)),
});

export const useSSIM = (shapeType: SSIMShapeType, enabled = true) => {
    const queryClient = useQueryClient();
    const {
        worker: ssim,
        rawWorker,
        isLoading: isLoadingWorker,
        isError: isWorkerError,
        error: workerError,
    } = useSSIMWorker(enabled);

    const [toolState, setToolState] = useState<SSIMState>(INITIAL_SSIM_STATE);
    const [ssimProps, setSSIMProps] = useState<RunSSIMProps | null>(null);
    // Results of a run that was reset or superseded must not repopulate the state.
    const runIdRef = useRef(0);

    const updateToolState = useCallback(
        (updatedProperties: Partial<SSIMState>) => {
            setToolState((currentState) => withShapes({ ...currentState, ...updatedProperties }, shapeType));
        },
        [shapeType]
    );

    const {
        mutate,
        reset: resetMutation,
        isPending,
        error: executionError,
    } = useMutation({
        mutationFn: async ({ props, runId }: SSIMRun) => {
            try {
                if (ssim === undefined) {
                    throw new Error('SSIM worker is not initialized yet');
                }

                return await executeWithTimeout(
                    ssim.executeSSIM(toToolRunSSIMProps(props)),
                    i18n.t('annotator.tools.ssim.label'),
                    SSIM_EXECUTE_TIMEOUT_MS
                );
            } catch (executeError) {
                // Comlink calls can't be cancelled and the worker runs them serially, so a stuck (or
                // never built) worker would block every later run: replace it instead.
                // A stale run must not tear down the worker a newer run is using.
                if (runId === runIdRef.current) {
                    rawWorker?.terminate();
                    void queryClient.resetQueries({ queryKey: SSIM_WORKER_QUERY_KEY });
                }

                throw executeError;
            }
        },
        onSuccess: (matches, { props, runId, keepNumberOfItems }) => {
            if (runId !== runIdRef.current) {
                return;
            }

            const { imageData, existingAnnotations, autoMergeDuplicates, template } = props;
            const ssimMatches = convertToolMatchesToGetiMatches(matches);
            const existingRects = autoMergeDuplicates ? getExistingRects(existingAnnotations) : [];
            const filteredMatches = filterSSIMResults(roiFromImage(imageData), ssimMatches, template, existingRects);

            setToolState((currentState) => {
                const threshold = keepNumberOfItems
                    ? clamp(currentState.threshold, 1, filteredMatches.length)
                    : guessNumberOfItemsThreshold(filteredMatches);

                return withShapes({ matches: filteredMatches, threshold }, shapeType);
            });
        },
        onError: (_error, { props, runId }) => {
            if (runId !== runIdRef.current) {
                return;
            }

            updateToolState({ matches: [{ shape: props.template, confidence: 1 }], threshold: 1 });
        },
    });

    const run = useCallback(
        (props: RunSSIMProps, keepNumberOfItems: boolean) => {
            runIdRef.current += 1;
            setSSIMProps(props);
            mutate({ props, runId: runIdRef.current, keepNumberOfItems });
        },
        [mutate]
    );

    const runSSIM = useCallback(
        (props: RunSSIMProps) => {
            // A new template replaces the pending preview instead of being merged into it.
            setToolState(INITIAL_SSIM_STATE);
            run(props, false);
        },
        [run]
    );

    // Keeps the current preview on screen until the new results arrive.
    const rerun = useCallback(
        (props: Partial<RunSSIMProps>) => {
            if (ssimProps !== null) {
                run({ ...ssimProps, ...props }, true);
            }
        },
        [ssimProps, run]
    );

    const reset = useCallback(() => {
        runIdRef.current += 1;
        setToolState(INITIAL_SSIM_STATE);
        setSSIMProps(null);
        resetMutation();
    }, [resetMutation]);

    const error = workerError ?? executionError;

    return useMemo(
        () => ({
            runSSIM,
            rerun,
            reset,
            updateToolState,
            toolState,
            isLoading: isLoadingWorker,
            isProcessing: isPending,
            isError: isWorkerError || executionError !== null,
            error,
            worker: ssim as Remote<SSIMWorkerInstance> | undefined,
        }),
        [
            runSSIM,
            rerun,
            reset,
            updateToolState,
            toolState,
            isLoadingWorker,
            isPending,
            isWorkerError,
            executionError,
            error,
            ssim,
        ]
    );
};
