// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, SetStateAction } from 'react';

import { Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

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
