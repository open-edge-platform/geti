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

import { useMemo } from 'react';

import isFunction from 'lodash/isFunction';

import { usePrediction } from '../../../providers/prediction-provider/prediction-provider.component';
import { useSubmitAnnotations } from '../../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { VideoControls } from '../video-controls/video-controls.interface';
import { useVideoPlayer } from '../video-player-provider.component';

export const useVideoControlsWithSaveConfirmation = (): VideoControls => {
    const { videoControls } = useVideoPlayer();
    const { setExplanationVisible } = usePrediction();
    const { confirmSaveAnnotations } = useSubmitAnnotations();

    return useMemo(() => {
        return {
            ...videoControls,
            goto: (frameNumber) => confirmSaveAnnotations(async () => videoControls.goto(frameNumber)),
            previous: () => confirmSaveAnnotations(async () => videoControls.previous()),
            next: () => confirmSaveAnnotations(async () => videoControls.next()),
            play: () =>
                confirmSaveAnnotations(async () => {
                    if (isFunction(videoControls.play)) {
                        videoControls.play();
                        setExplanationVisible(false);
                    }
                }),
        };
    }, [videoControls, confirmSaveAnnotations, setExplanationVisible]);
};
