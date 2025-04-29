// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
