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
