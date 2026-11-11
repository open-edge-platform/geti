// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { render } from '@testing-library/react';
import { MOCKED_VIDEO_PLAYER_CONTEXT } from 'mocks/mock-video-player-context';

import { VideoFrame } from './video-frame.component';
import { useVideoPlayer } from './video-player-provider.component';

rs.mock('./video-player-provider.component', () => ({
    useVideoPlayer: rs.fn(),
}));

describe('VideoFrame', () => {
    it.each([
        // The playback clock rounds to frame 3. The callback timestamp rounds to frame 2.
        { fps: 30, currentTime: 0.086, mediaTime: 0.066, expectedIndex: 2 },
        { fps: 7.5, currentTime: 0.134, mediaTime: 0.134, expectedIndex: 1 },
        { fps: 30, currentTime: 0, mediaTime: 0, expectedIndex: 0 },
    ])('tracks presented frame $expectedIndex at $fps fps', ({ fps, currentTime, mediaTime, expectedIndex }) => {
        const requestVideoFrameCallback = rs.fn((_callback: VideoFrameRequestCallback) => 1);
        const video = Object.assign(document.createElement('video'), {
            currentTime,
            requestVideoFrameCallback,
            cancelVideoFrameCallback: rs.fn(),
        });
        const drawImage = rs.fn();
        const canvas = Object.assign(document.createElement('canvas'), { getContext: () => ({ drawImage }) });
        const changeCurrentFrameIndex = rs.fn();

        rs.mocked(useVideoPlayer).mockReturnValue({
            ...MOCKED_VIDEO_PLAYER_CONTEXT,
            videoRef: { current: video },
            videoFrame: { ...MOCKED_VIDEO_PLAYER_CONTEXT.videoFrame, fps },
            videoControls: {
                ...MOCKED_VIDEO_PLAYER_CONTEXT.videoControls,
                isPlaying: true,
            },
            changeCurrentFrameIndex,
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
