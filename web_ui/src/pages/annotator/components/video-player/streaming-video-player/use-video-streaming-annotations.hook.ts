// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import isEmpty from 'lodash/isEmpty';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { PredictionMode } from '../../../../../core/annotations/services/prediction-service.interface';
import { VideoPaginationOptions } from '../../../../../core/annotations/services/video-pagination-options.interface';
import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { isVideoFrame, Video, VideoFrame } from '../../../../../core/media/video.interface';
import { isNonEmptyArray } from '../../../../../shared/utils';
import { ANNOTATOR_MODE } from '../../../core/annotation-tool-context.interface';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';
import { SelectedMediaItem } from '../../../providers/selected-media-item-provider/selected-media-item.interface';
import { useVideoAnnotationsQuery } from '../hooks/use-video-annotations-query.hook';
import { useVideoPredictionsQuery } from '../hooks/use-video-predictions-query.hook';
import { getVideoOptions } from './utils';

const getAnnotationsSelector = (frameNumber: number, neightbourSize: number) => {
    return (data: Record<number, Annotation[]>) => {
        if (data === null) {
            return null;
        }

        if (isNonEmptyArray(data[frameNumber])) {
            return { annotations: data[frameNumber], frameNumber };
        }

        for (let idx = 0; idx < neightbourSize; idx++) {
            if (isNonEmptyArray(data[frameNumber + idx])) {
                return { annotations: data[frameNumber + idx], frameNumber: frameNumber + idx };
            }
            if (isNonEmptyArray(data[frameNumber - idx])) {
                return { annotations: data[frameNumber - idx], frameNumber: frameNumber - idx };
            }
        }
        return null;
    };
};

const useStreamingVideoAnnotationsQuery = (
    video: Video,
    frameNumber: number,
    neighbourSize: number,
    options: VideoPaginationOptions,
    enabled = true
) => {
    const datasetIdentifier = useDatasetIdentifier();
    const selector = getAnnotationsSelector(frameNumber, neighbourSize);

    return useVideoAnnotationsQuery(datasetIdentifier, video, selector, options, enabled);
};

const useStreamingVideoPredictionsQuery = (
    video: Video,
    frameNumber: number,
    neighbourSize: number,
    options: VideoPaginationOptions,
    enabled = true
) => {
    const datasetIdentifier = useDatasetIdentifier();

    return useVideoPredictionsQuery(
        datasetIdentifier,
        video,
        getAnnotationsSelector(frameNumber, neighbourSize),
        options,
        PredictionMode.ONLINE,
        enabled
    );
};

// The backend returns maximally 20 predictions per request
const FRAMES_BUFFER_CHUNK_SIZE = 20;

export const useVideoStreamingAnnotations = (
    mediaItem: VideoFrame & Partial<SelectedMediaItem>,
    frameNumber: number,
    neighbourSize: number,
    mode: ANNOTATOR_MODE
) => {
    const video = {
        ...mediaItem,
        identifier: { type: MEDIA_TYPE.VIDEO, videoId: mediaItem.identifier.videoId },
    } as const;
    const options = getVideoOptions(video, frameNumber, neighbourSize, FRAMES_BUFFER_CHUNK_SIZE);

    const annotationsQuery = useStreamingVideoAnnotationsQuery(
        video,
        frameNumber,
        neighbourSize,
        options,
        mode === ANNOTATOR_MODE.ACTIVE_LEARNING
    );
    const predictionsQuery = useStreamingVideoPredictionsQuery(
        video,
        frameNumber,
        neighbourSize,
        options,
        mode === ANNOTATOR_MODE.PREDICTION
    );

    const annotations = useMemo(() => {
        if (
            mode === ANNOTATOR_MODE.ACTIVE_LEARNING &&
            annotationsQuery.data &&
            isNonEmptyArray(annotationsQuery.data.annotations)
        ) {
            return annotationsQuery.data.annotations;
        }

        if (
            mode === ANNOTATOR_MODE.PREDICTION &&
            predictionsQuery.data &&
            isNonEmptyArray(predictionsQuery.data.annotations)
        ) {
            return predictionsQuery.data.annotations;
        }
        return [];
    }, [annotationsQuery.data, predictionsQuery.data, mode]);

    if (mediaItem !== undefined && isVideoFrame(mediaItem) && mediaItem.identifier.frameNumber === frameNumber) {
        if (isEmpty(mediaItem.annotations) && mediaItem.predictions !== undefined) {
            return [...mediaItem.predictions.annotations];
        }

        if (mediaItem.annotations) {
            return mediaItem.annotations;
        }
    }

    return annotations;
};
