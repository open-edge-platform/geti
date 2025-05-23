// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery, UseQueryOptions } from '@tanstack/react-query';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { PredictionMode } from '../../../../../core/annotations/services/prediction-service.interface';
import { VideoPaginationOptions } from '../../../../../core/annotations/services/video-pagination-options.interface';
import { Video } from '../../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../../core/projects/dataset.interface';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';
import { useInferenceServerStatus } from '../../../providers/prediction-provider/use-inference-server-status';
import { useTask } from '../../../providers/task-provider/task-provider.component';

export const useVideoPredictionsQueryOptions = (
    datasetIdentifier: DatasetIdentifier,
    predictionMode: PredictionMode
) => {
    const { selectedTask, previousTask } = useTask();
    const { inferenceService } = useApplicationServices();
    const { project } = useProject();
    const { data = { isInferenceServerReady: false } } = useInferenceServerStatus(datasetIdentifier, true);

    return (video: Video, options: VideoPaginationOptions): UseQueryOptions => {
        const videoPredictionsQueryKey = [
            ...QUERY_KEYS.VIDEO_PREDICTIONS(datasetIdentifier, video.identifier, predictionMode, selectedTask, options),
        ];

        // Disable video predictions for subtasks, and make sure that the options' range contains at least 1 valid frame
        const enabled =
            data.isInferenceServerReady &&
            previousTask === null &&
            options.startFrame >= 0 &&
            options.startFrame < video.metadata.frames;

        return {
            queryKey: videoPredictionsQueryKey,
            queryFn: ({ signal }) => {
                return inferenceService.getVideoPredictions(
                    datasetIdentifier,
                    project.labels,
                    video,
                    predictionMode,
                    options,
                    signal
                );
            },
            enabled,
            // We want to manually clear the video annotations cache when the user switches to a different video
            gcTime: Infinity,
            staleTime: Infinity,
            // We only want to retry once to prevent us from ddos'ing the inference server
            retry: 1,
            meta: { disableGlobalErrorHandling: true },
        };
    };
};
export const useVideoPredictionsQuery = <T>(
    datasetIdentifier: DatasetIdentifier,
    video: Video,
    select: (data: Record<number, Annotation[]>) => T,
    options: VideoPaginationOptions,
    predictionMode: PredictionMode,
    enabled = true
) => {
    const getQueryOptions = useVideoPredictionsQueryOptions(datasetIdentifier, predictionMode);
    const queryOptions = getQueryOptions(video, options);

    return useQuery({
        ...queryOptions,
        // which is used to update the data via select
        // React query's type inference doesn't seem to work here
        enabled: enabled && queryOptions.enabled,
        // @ts-expect-error query options returns data of Record<number, Annotation[]>
        select,
    });
};
