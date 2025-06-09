// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef, useState } from 'react';

import { Button, dimensionValue, type ButtonProps } from '@geti/ui';
import { isNil, throttle } from 'lodash-es';

import { useEventListener } from '../../../../hooks/event-listener/event-listener.hook';
import { useCameraParams } from '../../hooks/camera-params.hook';

import classes from './action-buttons.module.scss';

interface CaptureButtonAnimationProps extends Omit<ButtonProps, 'variant'> {
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
            UNSAFE_style={{
                borderRadius: '50%',
                borderWidth: dimensionValue('size-50'),
            }}
            height={'size-900'}
        >
            {buttonProps.children}
        </Button>
    );
};
