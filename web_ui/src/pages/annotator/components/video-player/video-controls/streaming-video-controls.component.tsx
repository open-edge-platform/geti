// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { Flex, Loading } from '@geti/ui';
import { Play } from '@geti/ui/icons';
import { isEmpty, isFunction, isNil } from 'lodash-es';

import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';
import { useInferenceServerStatus } from '../../../providers/prediction-provider/use-inference-server-status';
import { useSelectedMediaItem } from '../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { getPreviousTask } from '../../../providers/task-chain-provider/utils';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { useStreamingVideoPlayer } from '../streaming-video-player/streaming-video-player-provider.component';
import { isFrameInLoadedBuffer } from '../streaming-video-player/utils';
import { getPlayTooltip } from '../utils';
import { Controls } from './video-controls.component';
import { VideoControls } from './video-controls.interface';
import { VolumeControls } from './volume-controls.component';

export interface usePauseResumeVideoBufferingProps {
    isPlaying: boolean;
    hasEmptyBuffers: boolean;
    isBufferedFrame: boolean;
    videoControls: VideoControls;
}

export const usePauseResumeVideoBuffering = ({
    isPlaying,
    isBufferedFrame,
    hasEmptyBuffers,
    videoControls,
}: usePauseResumeVideoBufferingProps) => {
    const isBufferPause = useRef(false);

    useEffect(() => {
        if (isPlaying && !hasEmptyBuffers && !isBufferedFrame) {
            isFunction(videoControls.pause) && videoControls.pause();
            isBufferPause.current = true;
        }

        if (!isPlaying && isBufferedFrame && isBufferPause.current) {
            isFunction(videoControls.play) && videoControls.play();
            isBufferPause.current = false;
        }
    }, [isBufferedFrame, hasEmptyBuffers, isPlaying, videoControls]);
};

export const StreamingVideoControls = ({ videoControls }: { videoControls: VideoControls }) => {
    const { tasks, selectedTask } = useTask();
    const { useProjectModelsQuery } = useModels();
    const datasetIdentifier = useDatasetIdentifier();
    const { selectedMediaItemQuery } = useSelectedMediaItem();
    const { isActiveLearningMode } = useAnnotatorMode();

    const isPredictionMode = !isActiveLearningMode;
    const { data: modelsData = [], isPending: isLoadingModels } = useProjectModelsQuery();
    const { data = { isInferenceServerReady: false } } = useInferenceServerStatus(datasetIdentifier, true);
    const hasModels = !isLoadingModels && !isEmpty(modelsData) && isPredictionMode;

    const previousTask = getPreviousTask(tasks, selectedTask);
    const { isMuted, setIsMuted, videoPlayerError, buffers, isBuffering, currentIndex, isPlaying } =
        useStreamingVideoPlayer();

    const isInSubTask = previousTask !== null;
    const isBufferedFrame = hasModels ? buffers.some(isFrameInLoadedBuffer(currentIndex)) : true;
    const isInferenceServerAndModelsReady = hasModels ? data.isInferenceServerReady : true;

    const isFetchingBuffer =
        isBuffering || !isInferenceServerAndModelsReady || !isBufferedFrame || selectedMediaItemQuery.isFetching;

    const playTooltip = getPlayTooltip(isInSubTask, isBufferedFrame, isInferenceServerAndModelsReady, videoPlayerError);

    const isDisabled = {
        previous: !videoControls.canSelectPrevious,
        next: !videoControls.canSelectNext,
        play: videoPlayerError !== undefined || isInSubTask || isFetchingBuffer,
        pause: videoPlayerError !== undefined,
    };

    usePauseResumeVideoBuffering({
        isPlaying,
        videoControls,
        isBufferedFrame,
        hasEmptyBuffers: isEmpty(buffers),
    });

    return (
        <Flex gap='size-100'>
            <Controls
                videoControls={videoControls}
                isDisabled={isDisabled}
                playTooltip={playTooltip}
                PlayIcon={() => {
                    return isFetchingBuffer && isNil(videoPlayerError) && !isInSubTask ? (
                        <Loading size={'S'} />
                    ) : (
                        <Play />
                    );
                }}
            />
            <VolumeControls isMuted={isMuted} setIsMuted={setIsMuted} />
        </Flex>
    );
};
