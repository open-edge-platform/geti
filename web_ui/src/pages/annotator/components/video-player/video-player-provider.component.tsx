// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, Dispatch, ReactNode, SetStateAction, useContext } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';

import { isVideoFrame, VideoFrame } from '../../../../core/media/video.interface';
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
