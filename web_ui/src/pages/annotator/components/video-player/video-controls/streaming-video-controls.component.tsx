// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useRef } from 'react';

import { Flex } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import isFunction from 'lodash/isFunction';
import isNil from 'lodash/isNil';

import { Play } from '../../../../../assets/icons';
import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { Loading } from '../../../../../shared/components/loading/loading.component';
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
