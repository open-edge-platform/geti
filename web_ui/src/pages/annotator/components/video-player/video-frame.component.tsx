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

import { RefObject } from 'react';

import { useSpinDelay } from 'spin-delay';

import { VideoFrame as VideoFrameInterface } from '../../../../core/media/video.interface';
import { LoadingIndicator } from '../../../../shared/components/loading/loading-indicator.component';
import { useRequestVideoFrameCallback } from '../../hooks/use-request-video-frame-callback.hook';
import { useStreamingVideoPlayer } from './streaming-video-player/streaming-video-player-provider.component';

export const VideoFrame = ({
    selectedMediaItem,
    canvasRef,
}: {
    selectedMediaItem: VideoFrameInterface;
    canvasRef: RefObject<HTMLCanvasElement>;
}) => {
    const { videoRef, isPlaying, setCurrentIndex, isBuffering } = useStreamingVideoPlayer();

    useRequestVideoFrameCallback(videoRef, selectedMediaItem.metadata.fps, (frameNumber) => {
        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');

            if (ctx === null || ctx === undefined || !videoRef.current) {
                return;
            }

            if (isPlaying) {
                ctx.drawImage(videoRef.current, 0, 0);
            }
        }

        if (!isPlaying) {
            return;
        }

        setCurrentIndex(frameNumber);
    });

    // Make it so that we only show the progress indicator if we're buffering for over 200ms,
    // any lower value seems to be not noticeable by the user
    const showBufferingIsInProgress = useSpinDelay(isPlaying && isBuffering, { delay: 200 });

    if (showBufferingIsInProgress) {
        return (
            <div style={{ position: 'absolute', inset: 0, backgroundColor: 'var(--white-hover)' }}>
                <LoadingIndicator size='L' />
            </div>
        );
    }

    return <></>;
};
