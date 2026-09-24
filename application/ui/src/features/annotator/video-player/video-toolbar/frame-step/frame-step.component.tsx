// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Dispatch, SetStateAction } from 'react';

import { useTranslation } from '@/i18n';
import { ActionButton, Tooltip, TooltipTrigger, View } from '@geti-ui/ui';
import { Fps } from '@geti-ui/ui/icons';

import { FRAME_STEP_TO_DISPLAY_ALL_FRAMES } from './utils';

import classes from './frame-step.module.scss';

type FrameStepProps = {
    step: number;
    onChangeStep: Dispatch<SetStateAction<number>>;
    isDisabled: boolean;
    defaultFps: number;
};

export const FrameStep = ({ isDisabled, step, onChangeStep, defaultFps }: FrameStepProps) => {
    const { t } = useTranslation();
    const isAllMode = step === FRAME_STEP_TO_DISPLAY_ALL_FRAMES;

    const handleFpsToggle = () => {
        onChangeStep((prevStep) => (prevStep === defaultFps ? FRAME_STEP_TO_DISPLAY_ALL_FRAMES : defaultFps));
    };

    return (
        <TooltipTrigger placement={'top'}>
            <ActionButton
                isQuiet
                isDisabled={isDisabled}
                onPress={handleFpsToggle}
                position={'relative'}
                aria-label={'Toggle frame mode'}
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
                >
                    {isAllMode ? t('common.labels.allUppercase') : '1/1'}
                </View>
            </ActionButton>
            <Tooltip>
                {isAllMode
                    ? t('annotator.video.playback.showOneFramePerSecond')
                    : t('annotator.video.playback.showAllFrames')}
            </Tooltip>
        </TooltipTrigger>
    );
};
