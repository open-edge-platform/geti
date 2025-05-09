// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { noop } from 'lodash-es';
import { useHotkeys } from 'react-hotkeys-hook';

import { KeyMap } from '../../shared/keyboard-events/keyboard.interface';

interface useIsPressedProps {
    key: KeyMap;
    onKeyUp?: (event: KeyboardEvent) => void;
    onKeyDown?: (event: KeyboardEvent) => void;
    predicated?: (event: KeyboardEvent) => boolean;
}
export const useIsPressed = ({ key, onKeyDown = noop, onKeyUp = noop, predicated = () => true }: useIsPressedProps) => {
    const [isPressed, setIsPressed] = useState(false);
    useHotkeys(
        key,
        (event) => {
            if (event.key === key && predicated(event)) {
                setIsPressed(true);
                onKeyDown(event);
            }
        },
        { keydown: true }
    );
    useHotkeys(
        key,
        (event) => {
            if (event.key === key) {
                setIsPressed(false);
                onKeyUp(event);
            }
        },
        { keyup: true }
    );

    return isPressed;
};
