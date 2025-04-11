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

import { createContext, Dispatch, ReactNode, SetStateAction, useContext } from 'react';

import { isVideoFrame, VideoFrame } from '../../../../core/media/video.interface';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { useStep } from './hooks/use-step.hook';
import { useVideoControls } from './hooks/use-video-controls.hook';
import { VideoControls } from './video-controls/video-controls.interface';

export interface VideoPlayerContextProps {
    step: number;
    videoFrame: VideoFrame;
    videoControls: VideoControls;
    setStep: Dispatch<SetStateAction<number>>;
}

export const VideoPlayerContext = createContext<VideoPlayerContextProps | undefined>(undefined);

interface VideoPlayerProviderProps {
    children: ReactNode;
    videoFrame: VideoFrame | undefined;
    selectVideoFrame: (videoFrame: VideoFrame) => void;
}

export const VideoPlayerProvider = ({
    children,
    videoFrame,
    selectVideoFrame,
}: VideoPlayerProviderProps): JSX.Element => {
    const [step, setStep] = useStep(videoFrame);

    // If the currently selected video frame is not part of the available video frames,
    // we will try to select the closest video frame
    // This allows us to easily switch between dataset and active dataset
    const videoControls = useVideoControls(videoFrame, selectVideoFrame, step);

    const value = isVideoFrame(videoFrame) ? { videoFrame, videoControls, step, setStep } : undefined;

    return <VideoPlayerContext.Provider value={value}>{children}</VideoPlayerContext.Provider>;
};

export const useVideoPlayer = (): VideoPlayerContextProps => {
    const context = useContext(VideoPlayerContext);

    if (context === undefined) {
        // TODO clarify that it can throw even if the VideoPlayerProvider has been rendered,
        // i.e. the user will need to select a VideoFrame
        throw new MissingProviderError('useVideoPlayer', 'VideoPlayerProvider');
    }

    return context;
};

export const useVideoPlayerContext = (): VideoPlayerContextProps | undefined => {
    return useContext(VideoPlayerContext);
};
