// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RefObject } from 'react';

import { Loading } from '@geti/ui';
import { useSpinDelay } from 'spin-delay';

import { VideoFrame as VideoFrameInterface } from '../../../../core/media/video.interface';
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
                <Loading mode='inline' size='L' />
            </div>
        );
    }

    return <></>;
};
