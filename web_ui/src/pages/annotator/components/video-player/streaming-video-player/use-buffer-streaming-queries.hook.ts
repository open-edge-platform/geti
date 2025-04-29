// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import sortBy from 'lodash/sortBy';

import { PredictionMode } from '../../../../../core/annotations/services/prediction-service.interface';
import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { isVideoFrame, VideoFrame } from '../../../../../core/media/video.interface';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
import { usePrevious } from '../../../../../hooks/use-previous/use-previous.hook';
import { ANNOTATOR_MODE } from '../../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';
import { useInferenceServerStatus } from '../../../providers/prediction-provider/use-inference-server-status';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import {
    Buffer,
    BufferStatus,
    getAdjustedNeighbourSize,
    getFilterForGroup,
    getNextBuffer,
    getVideoOptions,
} from './utils';

// The backend returns maximally 500 annotations per request
const FRAMES_CHUNK_SIZE = 20;

const useClearBuffersWhenSwitchingToADifferentMediaItem = (
    mediaItem: VideoFrame | undefined,
    setBuffers: (buffers: Buffer[]) => void
) => {
    const queryClient = useQueryClient();
    const previousMediaItem = usePrevious(mediaItem);

    const { selectedTask } = useTask();

    const datasetIdentifier = useDatasetIdentifier();

    useEffect(() => {
        if (mediaItem?.identifier.videoId === previousMediaItem?.identifier.videoId) {
            return;
        }

        if (previousMediaItem !== undefined) {
            const previousVideoIdentifier = {
                type: MEDIA_TYPE.VIDEO,
                videoId: previousMediaItem.identifier.videoId,
            } as const;

            const annotationsQueryKey = QUERY_KEYS.VIDEO_ANNOTATIONS(datasetIdentifier, previousVideoIdentifier);
            const predictionsQueryKey = QUERY_KEYS.VIDEO_PREDICTIONS(
                datasetIdentifier,
                previousVideoIdentifier,
                PredictionMode.ONLINE,
                selectedTask
            );
            setBuffers([]);
            queryClient.removeQueries({ queryKey: annotationsQueryKey });
            queryClient.removeQueries({ queryKey: predictionsQueryKey });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mediaItem?.identifier?.videoId]);
};

const useBuffersFromQueryClient = (mediaItem: VideoFrame | undefined) => {
    const queryClient = useQueryClient();
    const datasetIdentifier = useDatasetIdentifier();
    const { selectedTask, previousTask } = useTask();

    const buffers: Buffer[] = [];
    if (mediaItem === undefined || previousTask !== null) {
        return buffers;
    }

    const videoIdentifier = {
        type: MEDIA_TYPE.VIDEO as const,
        videoId: mediaItem.identifier.videoId,
    };

    const annotationsQueryKey = QUERY_KEYS.VIDEO_ANNOTATIONS(datasetIdentifier, videoIdentifier);
    const predictionsQueryKey = QUERY_KEYS.VIDEO_PREDICTIONS(
        datasetIdentifier,
        videoIdentifier,
        PredictionMode.ONLINE,
        selectedTask
    );

    [annotationsQueryKey, predictionsQueryKey].forEach((queryKey) => {
        // From the query client we determine the state of all
        // of this video's related annotation and prediction queries
        queryClient.getQueriesData({ queryKey }).forEach((query) => {
            // This type assertion should help us in making sure the query keys
            // used to parse the buffer properties remains correct
            const key = query[0] as
                | ReturnType<typeof QUERY_KEYS.VIDEO_ANNOTATIONS>
                | ReturnType<typeof QUERY_KEYS.VIDEO_PREDICTIONS>;

            const isLoading = query[1] === undefined;
            const mode = key[2];
            const selectedTaskId = mode === ANNOTATOR_MODE.ACTIVE_LEARNING ? null : (key[4] ?? null);
            const options = mode === ANNOTATOR_MODE.ACTIVE_LEARNING ? key[3] : key[5];

            if (
                options !== undefined &&
                options.startFrame !== undefined &&
                options.endFrame !== undefined &&
                options.frameSkip !== undefined
            ) {
                const status = isLoading ? BufferStatus.LOADING : BufferStatus.SUCCESS;
                buffers.push({
                    startFrame: options.startFrame,
                    endFrame: options.endFrame,
                    frameSkip: options.frameSkip,
                    status,
                    mode,
                    selectedTaskId,
                });
            }
        });
    });

    return sortBy(buffers, ({ startFrame }) => startFrame);
};

const joinOverlappingBuffers = (
    buffers: Buffer[],
    mode: ANNOTATOR_MODE,
    frameSkip: number,
    selectedTaskId: string | null
) => {
    // Only expose the buffers of the current configuration
    const buffersForGroup = buffers.filter(getFilterForGroup(mode, frameSkip, selectedTaskId));

    return buffersForGroup.reduce((combined: Buffer[], buffer: Buffer) => {
        const lastBuffer = combined.at(-1);

        if (lastBuffer === undefined) {
            return [buffer];
        }

        if (buffer.startFrame - lastBuffer.endFrame <= 1 && lastBuffer.status === buffer.status) {
            combined[combined.length - 1] = {
                ...lastBuffer,
                endFrame: buffer.endFrame,
            };
        } else {
            combined.push(buffer);
        }

        return combined;
    }, []);
};

export const useBufferStreamingQueries = (
    mediaItem: VideoFrame | undefined,
    currentIndex: number,
    playbackRate: number,
    neighbourSize: number
) => {
    // Currently we only use the buffers state variable to force rerender this hook,
    // this makes it os that we "recompute" the buffers for the current video
    const [_, setBuffers] = useState<Buffer[]>([]);
    useClearBuffersWhenSwitchingToADifferentMediaItem(mediaItem, setBuffers);

    const { isActiveLearningMode, currentMode } = useAnnotatorMode();
    const { selectedTask, previousTask } = useTask();
    const buffers = useBuffersFromQueryClient(mediaItem);

    // Don't return any buffers if the user is fetching predictions but the inference server isn't ready
    const datasetIdentifier = useDatasetIdentifier();
    const { data = { isInferenceServerReady: false } } = useInferenceServerStatus(
        datasetIdentifier,
        isVideoFrame(mediaItem)
    );
    if (data.isInferenceServerReady === false && !isActiveLearningMode) {
        return { buffers: [], nextBuffer: undefined, setBuffers };
    }

    if (mediaItem === undefined) {
        return { buffers: [], nextBuffer: undefined, setBuffers };
    }

    const fps = mediaItem.metadata.fps;
    const adjustedNeighbourSize = getAdjustedNeighbourSize(fps, playbackRate, neighbourSize);
    const options = getVideoOptions(mediaItem, currentIndex, adjustedNeighbourSize, FRAMES_CHUNK_SIZE);

    const selectedTaskId = selectedTask?.id ?? null;
    const nextBuffer =
        previousTask !== null
            ? undefined
            : getNextBuffer(
                  {
                      ...mediaItem,
                      identifier: { ...mediaItem.identifier, frameNumber: currentIndex },
                  },
                  buffers.filter((buffer) => buffer.mode === currentMode),
                  currentMode,
                  adjustedNeighbourSize,
                  selectedTaskId
              );

    // By joining overlapping buffers we can make sure that we render less elements
    // when visualizing the buffer state in the video player's slider
    const joinedBuffers = joinOverlappingBuffers(buffers, currentMode, options.frameSkip, selectedTaskId);

    return { buffers: joinedBuffers, nextBuffer, setBuffers };
};
