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

import { useStreamingVideoPlayerContext } from '../components/video-player/streaming-video-player/streaming-video-player-provider.component';
import { useVideoPlayerContext } from '../components/video-player/video-player-provider.component';
import { useSelectedMediaItem } from '../providers/selected-media-item-provider/selected-media-item-provider.component';

export enum SceneState {
    IDLE = 'IDLE',
    LOADING = 'LOADING',
    VIDEO_IS_PLAYING = 'VIDEO_IS_PLAYING',
}

export const useAnnotatorSceneInteractionState = (): { interactionState: SceneState } => {
    const { selectedMediaItemQuery } = useSelectedMediaItem();
    const streamingVideoPlayerContext = useStreamingVideoPlayerContext();
    const videoPlayerContext = useVideoPlayerContext();

    if (selectedMediaItemQuery.isFetching) {
        return { interactionState: SceneState.LOADING };
    }

    if (streamingVideoPlayerContext) {
        if (streamingVideoPlayerContext.isPlaying) {
            return { interactionState: SceneState.VIDEO_IS_PLAYING };
        } else {
            return { interactionState: SceneState.IDLE };
        }
    } else if (videoPlayerContext) {
        const {
            videoControls: { isPlaying },
        } = videoPlayerContext;

        if (isPlaying) {
            return { interactionState: SceneState.VIDEO_IS_PLAYING };
        }
    }

    return { interactionState: SceneState.IDLE };
};

export const useIsSceneBusy = (): boolean => {
    const { interactionState } = useAnnotatorSceneInteractionState();

    return interactionState !== SceneState.IDLE;
};
