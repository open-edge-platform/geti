// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useRef } from 'react';

import { screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { getMockedVideoFrameMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { annotatorRender as render } from '../../test-utils/annotator-render';
import { useStreamingVideoPlayer } from './streaming-video-player/streaming-video-player-provider.component';
import { VideoFrame } from './video-frame.component';

jest.mock('./streaming-video-player/streaming-video-player-provider.component', () => ({
    ...jest.requireActual('./streaming-video-player/streaming-video-player-provider.component'),
    useStreamingVideoPlayer: jest.fn(),
}));

describe('VideoFrame', () => {
    it('does not show a loading indicator if it is not buffering', async () => {
        // @ts-expect-error we only want to mock values related to isBuffering state
        jest.mocked(useStreamingVideoPlayer).mockImplementation(() => ({
            isPlaying: true,
            isBuffering: false,
            videoRef: {
                current: null,
            },
        }));

        const canvasRef = { current: null };
        const videoFrame = getMockedVideoFrameMediaItem({});

        render(<VideoFrame selectedMediaItem={videoFrame} canvasRef={canvasRef} />);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('informs the user the video is buffering', async () => {
        // @ts-expect-error we only want to mock values related to isBuffering state
        jest.mocked(useStreamingVideoPlayer).mockImplementation(() => ({
            isPlaying: true,
            isBuffering: true,
            videoRef: {
                current: null,
            },
        }));

        const canvasRef = { current: null };
        const videoFrame = getMockedVideoFrameMediaItem({});

        render(<VideoFrame selectedMediaItem={videoFrame} canvasRef={canvasRef} />);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(await screen.findByRole('progressbar')).toBeInTheDocument();
    });

    it('updates the currently viewed video frame', async () => {
        const setCurrentIndex = jest.fn();
        const videoFrame = getMockedVideoFrameMediaItem({});

        const App = () => {
            const canvasRef = useRef<HTMLCanvasElement>(null);
            const videoRef = useRef<HTMLVideoElement>(null);

            // @ts-expect-error we only want to mock values related to isBuffering state
            jest.mocked(useStreamingVideoPlayer).mockImplementation(() => ({
                isPlaying: true,
                isBuffering: true,
                videoRef,
                setCurrentIndex,
            }));

            return (
                <>
                    <canvas ref={canvasRef} />
                    {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
                    <video ref={videoRef} />
                    <VideoFrame selectedMediaItem={videoFrame} canvasRef={canvasRef} />
                </>
            );
        };
        render(<App />);

        await waitFor(() => {
            expect(setCurrentIndex).toHaveBeenCalledWith(0);
        });
    });
});
