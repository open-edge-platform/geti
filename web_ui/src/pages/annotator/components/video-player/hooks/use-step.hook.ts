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
