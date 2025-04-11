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
