// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useRef, useState } from 'react';

import { SpectrumButtonProps } from '@adobe/react-spectrum';
import isNil from 'lodash/isNil';
import throttle from 'lodash/throttle';

import { useEventListener } from '../../../../hooks/event-listener/event-listener.hook';
import { Button } from '../../../../shared/components/button/button.component';
import { useCameraParams } from '../../hooks/camera-params.hook';

import classes from './action-buttons.module.scss';

interface CaptureButtonAnimationProps extends Omit<SpectrumButtonProps, 'variant'> {
    onPress: () => void;
    videoTag?: HTMLVideoElement | null;
}

export const MOUSE_HOLD_TIMER = 500;
const NUMBER_OF_CALLS_INTERVAL = 50; // 20 calls per second (50ms interval)

const throttledAnimation = throttle(
    (videoTag: CaptureButtonAnimationProps['videoTag']) => videoTag?.classList.add(classes.takeFlash),
    MOUSE_HOLD_TIMER
);

const addAnimationClasses = (videoTag: CaptureButtonAnimationProps['videoTag']) => {
    videoTag?.classList.add(classes.takeFlash);
    videoTag?.classList.add(classes.takeOldCamera);
};

const removeAnimationClasses = (videoTag: CaptureButtonAnimationProps['videoTag']) => {
    videoTag?.classList.remove(classes.takeFlash);
    videoTag?.classList.remove(classes.takeOldCamera);
};

export const CaptureButtonAnimation = ({
    videoTag,
    onPress,
    ...buttonProps
}: CaptureButtonAnimationProps): JSX.Element => {
    const intervalId = useRef<ReturnType<typeof setInterval> | null>(null);
    const timerId = useRef<ReturnType<typeof setTimeout> | null>(null);
    const { isLivePrediction } = useCameraParams();

    const [isPressing, setIsPressing] = useState(false);

    const handleOnPressStart = () => {
        // Start timeout and add animation classes
        addAnimationClasses(videoTag);
        setIsPressing(false);

        timerId.current = setTimeout(() => {
            setIsPressing(true);
            !isLivePrediction ? handleLongPress() : onPress();
        }, MOUSE_HOLD_TIMER);
    };

    const handleOnPressEnd = () => {
        // Clear timeout and interval
        if (timerId.current) {
            clearTimeout(timerId.current);
        }

        if (intervalId.current) {
            clearInterval(intervalId.current);
        }

        if (!isPressing) {
            onPress();
        }

        setIsPressing(false);
    };

    const handleLongPress = () => {
        intervalId.current = setInterval(() => {
            // While the mouse is being held we want to
            // add the blinking animation to give the user some feedback
            throttledAnimation(videoTag);

            onPress();
        }, NUMBER_OF_CALLS_INTERVAL);
    };

    useEventListener('animationend', () => removeAnimationClasses(videoTag), videoTag);

    useEffect(() => {
        // Make sure we REALLY clear the timeout and the interval
        return () => {
            timerId.current && clearTimeout(timerId.current);
            intervalId.current && clearInterval(intervalId.current);
        };
    }, []);

    return (
        <Button
            variant='primary'
            {...buttonProps}
            aria-label='photo capture'
            isDisabled={isNil(videoTag)}
            onPressStart={handleOnPressStart}
            onPressEnd={handleOnPressEnd}
        >
            {buttonProps.children}
        </Button>
    );
};
