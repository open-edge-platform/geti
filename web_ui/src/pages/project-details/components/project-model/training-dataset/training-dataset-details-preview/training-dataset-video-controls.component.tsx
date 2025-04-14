// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Controls } from '../../../../../annotator/components/video-player/video-controls/video-controls.component';
import { checkIfCanSelectNext, checkIfCanSelectPrevious, goNext, goPrevious } from './utils';

interface TrainingDatasetVideoControlsProps {
    frameNumber: number;
    frames: number[];
    selectFrame: (frameNumber: number) => void;
}

export const TrainingDatasetVideoControls = ({
    frameNumber,
    frames,
    selectFrame,
}: TrainingDatasetVideoControlsProps): JSX.Element => {
    const canSelectPrevious = checkIfCanSelectPrevious(frameNumber, frames);

    const canSelectNext = checkIfCanSelectNext(frameNumber, frames);

    const goPreviousHandler = () => {
        goPrevious(frameNumber, frames, selectFrame);
    };

    const goNextHandler = () => {
        goNext(frameNumber, frames, selectFrame);
    };

    const videoControls = {
        canSelectPrevious,
        previous: goPreviousHandler,
        canSelectNext,
        isPlaying: false,
        next: goNextHandler,
        goto: selectFrame,
    };

    return <Controls videoControls={videoControls} />;
};
