// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useEffect, useState } from 'react';

import { isVideoFrame, VideoFrame } from '../../../../../core/media/video.interface';
import { usePrevious } from '../../../../../hooks/use-previous/use-previous.hook';

export const useStep = (videoFrame: VideoFrame | undefined): [number, Dispatch<SetStateAction<number>>] => {
    const frameStride = isVideoFrame(videoFrame) ? videoFrame.metadata.frameStride : 1;
    const videoId = videoFrame?.identifier?.videoId;
    const previousVideoId = usePrevious(videoId);

    // Reset the step when the selected video changes
    const [step, setStep] = useState(frameStride);

    useEffect(() => {
        if (videoId !== previousVideoId) {
            setStep(frameStride);
        }
    }, [frameStride, videoId, previousVideoId]);

    return [step, setStep];
};
