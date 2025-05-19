// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { Tooltip, TooltipTrigger, View } from '@geti/ui';

import { Fps } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { FRAME_STEP_TO_DISPLAY_ALL_FRAMES } from '../../utils';

import classes from './frame-step.module.scss';

interface FrameStepProps {
    step: number;
    setStep: Dispatch<SetStateAction<number>>;
    isDisabled: boolean;
    defaultFps: number;
}

enum FrameMode {
    // Note: All mode means we display all the frames, so the frame skip is equal to 1
    // One frame means we display one frame per second, so the frame skip is 60
    ALL_FRAMES = 'ALL',
    ONE_FRAME = '1/1',
}

export const FrameStep = ({ isDisabled, step, setStep, defaultFps }: FrameStepProps): JSX.Element => {
    const isAllMode = step === FRAME_STEP_TO_DISPLAY_ALL_FRAMES;

    const handleFpsToggle = () => {
        setStep((prevStep) => (prevStep === defaultFps ? FRAME_STEP_TO_DISPLAY_ALL_FRAMES : defaultFps));
    };

    return (
        <TooltipTrigger placement={'top'}>
            <QuietActionButton
                isDisabled={isDisabled}
                onPress={handleFpsToggle}
                position={'relative'}
                aria-label={'Toggle frame mode'}
                id={`toggle-frame-mode-id-${step}`}
            >
                <Fps />
                <View
                    position={'absolute'}
                    top={0}
                    right={-5}
                    paddingY={'size-25'}
                    paddingX={'size-50'}
                    UNSAFE_className={classes.frameStepBadge}
                    data-testid={'frame-mode-indicator-id'}
                    id={'frame-mode-indicator-id'}
                >
                    {isAllMode ? FrameMode.ALL_FRAMES : FrameMode.ONE_FRAME}
                </View>
            </QuietActionButton>
            <Tooltip>{isAllMode ? 'Show 1 frame per second' : 'Show all frames'}</Tooltip>
        </TooltipTrigger>
    );
};
