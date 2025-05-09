// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { QueryKey, useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isFunction } from 'lodash-es';

import {
    PredictionCache,
    PredictionId,
    PredictionMode,
    PredictionResult,
} from '../../../../core/annotations/services/prediction-service.interface';
import { getPredictionCache } from '../../../../core/annotations/services/utils';
import { Label } from '../../../../core/labels/label.interface';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { isVideoFrame } from '../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { isKeypointDetection } from '../../../../core/projects/domains';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';
import { useTask } from '../task-provider/task-provider.component';
import { updateVideoTimelineQuery } from './utils';

interface UseGetPredictions {
    taskId?: string;
    enabled?: boolean;
    mediaItem: MediaItem | undefined;
    predictionId?: PredictionId;
    coreLabels: Label[];
    datasetIdentifier: DatasetIdentifier;
    onError?: (error: AxiosError) => void;
    onSuccess?: (predictions: PredictionResult) => void;
}

export const usePredictionsQuery = ({
    taskId,
    mediaItem,
    enabled = true,
    coreLabels,
    datasetIdentifier,
    predictionId = PredictionMode.AUTO,
    onSuccess,
    onError,
}: UseGetPredictions): {
    predictionsQuery: UseQueryResult<PredictionResult, AxiosError>;
} => {
    const queryClient = useQueryClient();
    const { selectedTask, tasks } = useTask();
    const { inferenceService, visualPromptService } = useApplicationServices();

    const isTaskChainProject = tasks.length > 1;
    const predictionCache = getPredictionCache(predictionId);
    const isPredictionCacheAuto = predictionCache === PredictionCache.AUTO;
    const isPredictionCacheNever = predictionCache === PredictionCache.NEVER;
    const isQueryEnabled = enabled && mediaItem !== undefined;

    const isKeypointDetectionTask = selectedTask !== null && isKeypointDetection(selectedTask.domain);
    const shouldFetchExplanations = isPredictionCacheNever && !isKeypointDetectionTask;

    const queryKey: QueryKey = [
        ...QUERY_KEYS.SELECTED_MEDIA_ITEM.PREDICTIONS(mediaItem?.identifier, 'initial', predictionCache, taskId),
        predictionId,
    ];

    const handleSuccessRef = useRef(onSuccess);
    const handleErrorRef = useRef(onError);

    // TODO: extract explanations
    const predictionsQuery = useQuery<PredictionResult, AxiosError>({
        queryKey,
        queryFn: async ({ signal }) => {
            if (mediaItem === undefined) {
                throw new Error("Can't fetch undefined media item");
            }

            if (predictionId === PredictionMode.VISUAL_PROMPT) {
                const annotations = await visualPromptService.infer(
                    datasetIdentifier,
                    coreLabels,
                    mediaItem,
                    taskId ?? tasks[0].id,
                    signal
                );

                return {
                    maps: [],
                    annotations,
                };
            }

            const explainPromise = shouldFetchExplanations
                ? inferenceService.getExplanations(
                      datasetIdentifier,
                      mediaItem,
                      isTaskChainProject ? taskId : undefined,
                      undefined,
                      signal
                  )
                : Promise.resolve([]);

            const predictionsPromise = inferenceService.getPredictions(
                datasetIdentifier,
                coreLabels,
                mediaItem,
                predictionCache,
                isTaskChainProject ? taskId : undefined,
                undefined,
                signal
            );

            const [annotationsResponse, explanationResponse] = await Promise.allSettled([
                predictionsPromise,
                explainPromise,
            ]);

            return {
                maps: explanationResponse.status === 'fulfilled' ? explanationResponse.value : [],
                annotations: annotationsResponse.status === 'fulfilled' ? annotationsResponse.value : [],
            };
        },
        enabled: isQueryEnabled,
        retry: isPredictionCacheAuto ? 0 : 2,
        // When the user has opened the annotator we won't refresh the predictions
        // while they are on the same image
        staleTime: 5 * 60_000,
        gcTime: 0,
    });

    useEffect(() => {
        handleSuccessRef.current = onSuccess;
    }, [onSuccess]);

    useEffect(() => {
        handleErrorRef.current = onError;
    }, [onError]);

    useEffect(() => {
        if (!isQueryEnabled || !predictionsQuery.isSuccess) {
            return;
        }

        const predictions = predictionsQuery.data;

        if (isVideoFrame(mediaItem)) {
            const videoTimelineQueryKeyPrefix = QUERY_KEYS.VIDEO_PREDICTIONS(
                datasetIdentifier,
                { type: MEDIA_TYPE.VIDEO, videoId: mediaItem.identifier.videoId },
                PredictionMode.LATEST,
                selectedTask
            );

            updateVideoTimelineQuery(queryClient, videoTimelineQueryKeyPrefix, mediaItem, predictions.annotations);
        }

        if (isFunction(handleSuccessRef.current)) {
            handleSuccessRef.current(predictions);
        }
    }, [
        isQueryEnabled,
        predictionsQuery.isSuccess,
        predictionsQuery.data,
        queryClient,
        datasetIdentifier,
        mediaItem,
        selectedTask,
    ]);

    useEffect(() => {
        if (!predictionsQuery.isError || handleErrorRef.current === undefined) {
            return;
        }

        handleErrorRef.current(predictionsQuery.error);
    }, [predictionsQuery.isError, predictionsQuery.error]);

    return { predictionsQuery };
};
