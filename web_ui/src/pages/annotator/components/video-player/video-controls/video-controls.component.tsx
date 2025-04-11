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

import { ButtonGroup } from '@adobe/react-spectrum';
import isFunction from 'lodash/isFunction';

import { Pause, Play, StepBackward, StepForward } from '../../../../../assets/icons';
import { TooltipWithDisableButton } from '../../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { useVideoKeyboardShortcuts } from '../../../hot-keys/use-video-keyboard-shortcuts/use-video-keyboard-shortcuts';
import { VideoControls } from './video-controls.interface';

interface ControlsProps {
    videoControls: VideoControls;
    isDisabled?: {
        next: boolean;
        previous: boolean;
        play: boolean;
        pause: boolean;
    };
    PlayIcon?: () => JSX.Element;
    playTooltip?: string | undefined;
}

const TOOLTIP = {
    previous: 'Go to previous frame',
    next: 'Go to next frame',
    play: 'Play video',
    pause: 'Pause video',
};

export const Controls = ({
    videoControls,
    PlayIcon = () => <Play />,
    isDisabled = { next: false, previous: false, play: false, pause: false },
    playTooltip = TOOLTIP.play,
}: ControlsProps): JSX.Element => {
    const hasPlayAndPause = isFunction(videoControls.play) && isFunction(videoControls.pause);
    useVideoKeyboardShortcuts(videoControls);

    const isPlayDisabled = isDisabled?.play || videoControls.canPlay === false;

    return (
        <ButtonGroup aria-label='Video controls'>
            <TooltipWithDisableButton
                placement={'bottom'}
                activeTooltip={TOOLTIP.previous}
                disabledTooltip={TOOLTIP.previous}
            >
                <QuietActionButton
                    id='video-player-go-to-previous-frame'
                    aria-label={TOOLTIP.previous}
                    onPress={videoControls.previous}
                    isDisabled={isDisabled.previous || !videoControls.canSelectPrevious}
                >
                    <StepBackward />
                </QuietActionButton>
            </TooltipWithDisableButton>

            {hasPlayAndPause &&
                (videoControls.isPlaying ? (
                    <TooltipWithDisableButton
                        placement={'bottom'}
                        activeTooltip={TOOLTIP.pause}
                        disabledTooltip={TOOLTIP.pause}
                    >
                        <QuietActionButton
                            id='video-player-pause'
                            aria-label={TOOLTIP.pause}
                            onPress={videoControls.pause}
                            isDisabled={isDisabled.pause}
                        >
                            <Pause />
                        </QuietActionButton>
                    </TooltipWithDisableButton>
                ) : (
                    <TooltipWithDisableButton
                        placement={'bottom'}
                        activeTooltip={playTooltip}
                        disabledTooltip={playTooltip}
                    >
                        <QuietActionButton
                            id='video-player-play'
                            aria-label={TOOLTIP.play}
                            onPress={videoControls.play}
                            isDisabled={isPlayDisabled}
                        >
                            <PlayIcon />
                        </QuietActionButton>
                    </TooltipWithDisableButton>
                ))}

            <TooltipWithDisableButton placement={'bottom'} activeTooltip={TOOLTIP.next} disabledTooltip={TOOLTIP.next}>
                <QuietActionButton
                    id='video-player-go-to-next-frame'
                    aria-label={TOOLTIP.next}
                    onPress={videoControls.next}
                    isDisabled={isDisabled.next || !videoControls.canSelectNext}
                >
                    <StepForward />
                </QuietActionButton>
            </TooltipWithDisableButton>
        </ButtonGroup>
    );
};
