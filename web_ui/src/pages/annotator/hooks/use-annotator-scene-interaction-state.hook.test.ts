// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { useStreamingVideoPlayerContext } from '../components/video-player/streaming-video-player/streaming-video-player-provider.component';
import { SceneState, useAnnotatorSceneInteractionState } from './use-annotator-scene-interaction-state.hook';

let mockReadyState: number;
let mockIsPlaying: boolean;
let mockIsLoading: boolean;

jest.mock('../components/video-player/streaming-video-player/streaming-video-player-provider.component', () => {
    return {
        ...jest.requireActual(
            '../components/video-player/streaming-video-player/streaming-video-player-provider.component'
        ),
        useStreamingVideoPlayerContext: jest.fn(),
    };
});

jest.mock('../providers/selected-media-item-provider/selected-media-item-provider.component', () => ({
    ...jest.requireActual('../providers/selected-media-item-provider/selected-media-item-provider.component'),
    useSelectedMediaItem: jest.fn(() => ({ selectedMediaItemQuery: { isFetching: mockIsLoading } })),
}));

jest.mock('../components/video-player/video-player-provider.component', () => ({
    ...jest.requireActual('../components/video-player/video-player-provider.component'),
    useVideoPlayerContext: jest.fn(() => ({
        videoControls: { isPlaying: mockIsPlaying },
    })),
}));

describe('useAnnotatorSceneInteractionState', () => {
    beforeEach(() => {
        mockReadyState = 0;
        mockIsPlaying = false;
        mockIsLoading = false;
        (useStreamingVideoPlayerContext as jest.Mock).mockImplementation(() => ({
            readyState: mockReadyState,
            isPlaying: mockIsPlaying,
        }));
    });

    it('IDLE is default', () => {
        mockReadyState = 4;
        const {
            result: {
                current: { interactionState },
            },
        } = renderHook(() => useAnnotatorSceneInteractionState());
        expect(interactionState).toEqual(SceneState.IDLE);
    });

    it('LOADING when selectedMediaItemQuery.isPending is true', () => {
        mockReadyState = 4;
        mockIsPlaying = true;
        mockIsLoading = true;
        const {
            result: {
                current: { interactionState },
            },
        } = renderHook(() => useAnnotatorSceneInteractionState());
        expect(interactionState).toEqual(SceneState.LOADING);
    });

    it('ignores the readyState', () => {
        mockReadyState = 1;
        const {
            result: {
                current: { interactionState },
            },
        } = renderHook(() => useAnnotatorSceneInteractionState());
        expect(interactionState).toEqual(SceneState.IDLE);
    });

    it('VIDEO_IS_PLAYING when isPlaying is true', () => {
        mockReadyState = 3;
        mockIsPlaying = true;
        const {
            result: {
                current: { interactionState },
            },
        } = renderHook(() => useAnnotatorSceneInteractionState());
        expect(interactionState).toEqual(SceneState.VIDEO_IS_PLAYING);
    });

    it('VIDEO_IS_PLAYING when isPlaying is true and no streaming context', () => {
        mockReadyState = 3;
        mockIsPlaying = true;
        (useStreamingVideoPlayerContext as jest.Mock).mockImplementationOnce(() => null);
        const {
            result: {
                current: { interactionState },
            },
        } = renderHook(() => useAnnotatorSceneInteractionState());
        expect(interactionState).toEqual(SceneState.VIDEO_IS_PLAYING);
    });
});
