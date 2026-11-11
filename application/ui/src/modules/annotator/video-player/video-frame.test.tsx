// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { render } from '@testing-library/react';
import { getMockedVideoFrame } from 'mocks/mock-media';

import { VideoFrame } from './video-frame.component';
import { useVideoPlayer } from './video-player-provider.component';

rs.mock('./video-player-provider.component', () => ({
    useVideoPlayer: rs.fn(),
}));

describe('VideoFrame', () => {
    it.each([
        { fps: 30, playbackTime: 0.086, mediaTime: 0.066, expectedIndex: 2 },
        { fps: 7.5, playbackTime: 0.134, mediaTime: 0.134, expectedIndex: 1 },
        { fps: 30, playbackTime: 0, mediaTime: 0, expectedIndex: 0 },
    ])('tracks frame $expectedIndex at $fps fps', ({ fps, playbackTime, mediaTime, expectedIndex }) => {
        const requestVideoFrameCallback = rs.fn((_callback: VideoFrameRequestCallback) => 1);
        const video = Object.assign(document.createElement('video'), {
            currentTime: playbackTime,
            requestVideoFrameCallback,
            cancelVideoFrameCallback: rs.fn(),
        });
        const drawImage = rs.fn();
        const canvas = Object.assign(document.createElement('canvas'), { getContext: () => ({ drawImage }) });
        const changeCurrentFrameIndex = rs.fn();

        rs.mocked(useVideoPlayer).mockReturnValue({
            videoRef: { current: video },
            videoFrame: getMockedVideoFrame({ fps }),
            videoControls: {
                isPlaying: true,
                canSelectPreviousFrame: false,
                canSelectNextFrame: true,
                previousFrame: rs.fn(),
                nextFrame: rs.fn(),
                play: rs.fn(() => Promise.resolve()),
                pause: rs.fn(),
                goto: rs.fn(),
            },
            changeCurrentFrameIndex,
            isMuted: false,
            toggleMute: rs.fn(),
            playbackRate: 1,
            changePlaybackRate: rs.fn(),
            step: 1,
            changeStep: rs.fn(),
            videoError: null,
        });

        render(<VideoFrame canvasRef={{ current: canvas }} />);
        const [callback] = requestVideoFrameCallback.mock.calls[0];
        callback(0, {
            mediaTime,
            expectedDisplayTime: 0,
            presentationTime: 0,
            presentedFrames: 1,
            width: 32,
            height: 32,
        });

        expect(drawImage).toHaveBeenCalledWith(video, 0, 0);
        expect(changeCurrentFrameIndex).toHaveBeenCalledWith(expectedIndex);
    });
});
