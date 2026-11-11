// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { useVideoPlayer } from '../src/modules/annotator/video-player/video-player-provider.component';
import { getMockedVideoFrame } from './mock-media';

export const MOCKED_VIDEO_PLAYER_CONTEXT = {
    videoRef: { current: null },
    videoFrame: getMockedVideoFrame({
        fps: 60,
        frame_count: 600,
        frame_number: 42,
        frame_stride: 1,
        duration: 10,
    }),
    step: 1,
    changeStep: rs.fn(),
    isMuted: false,
    toggleMute: rs.fn(),
    playbackRate: 1,
    changePlaybackRate: rs.fn(),
    videoControls: {
        isPlaying: false,
        play: rs.fn(() => Promise.resolve()),
        pause: rs.fn(),
        goto: rs.fn(),
        previousFrame: rs.fn(),
        nextFrame: rs.fn(),
        canSelectPreviousFrame: true,
        canSelectNextFrame: true,
    },
    changeCurrentFrameIndex: rs.fn(),
    videoError: null,
} satisfies ReturnType<typeof useVideoPlayer>;
