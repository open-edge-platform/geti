// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import noop from 'lodash/noop';
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
