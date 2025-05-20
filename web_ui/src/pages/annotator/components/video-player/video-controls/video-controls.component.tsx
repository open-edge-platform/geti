// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ButtonGroup } from '@geti/ui';
import { Pause, Play, StepBackward, StepForward } from '@geti/ui/icons';
import { isFunction } from 'lodash-es';

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
