// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useMemo } from 'react';

import { VideoFrame } from '../../../../../core/media/video.interface';
import { VideoControls } from './../video-controls/video-controls.interface';
import { useConstructVideoFrame } from './use-construct-video-frame.hook';
import { usePlayVideo } from './use-play-video.hook';

export const useVideoControls = (
    videoFrame: VideoFrame | undefined,
    selectVideoFrame: (videoFrame: VideoFrame) => void,
    step: number
): VideoControls => {
    const constructVideoFrame = useConstructVideoFrame(videoFrame);

    const selectFrame = useCallback(
        (frameNumber: number) => {
            const newVideoFrame = constructVideoFrame(frameNumber);

            if (newVideoFrame) {
                selectVideoFrame(newVideoFrame);
            }
        },
        [selectVideoFrame, constructVideoFrame]
    );

    const [isPlaying, setIsPlaying] = usePlayVideo(videoFrame, step, selectFrame);

    const currentFrameNumber = videoFrame?.identifier?.frameNumber ?? 0;
    const totalFrames = videoFrame?.metadata?.frames ?? 1;
    const videoControls: VideoControls = useMemo(() => {
        const round = (x: number) => Math.round(x / step) * step;
        const previousVideoFrameNumber = round(currentFrameNumber - step);
        const canSelectPrevious = previousVideoFrameNumber >= 0;

        const nextVideoFrameNumber = round(currentFrameNumber + step);
        const canSelectNext = nextVideoFrameNumber < totalFrames;

        const pause = () => {
            setIsPlaying(false);
        };

        const previous = () => {
            if (canSelectPrevious) {
                pause();

                selectFrame(previousVideoFrameNumber);
            }
        };

        const next = () => {
            if (canSelectNext) {
                pause();

                selectFrame(nextVideoFrameNumber);
            }
        };
        const play = () => setIsPlaying(true);

        const goto = (frameNumber: number) => {
            pause();

            selectFrame(frameNumber);
        };

        return { isPlaying, canSelectPrevious, previous, canSelectNext, next, play, pause, goto };
    }, [selectFrame, isPlaying, setIsPlaying, step, currentFrameNumber, totalFrames]);

    return videoControls;
};
