// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
