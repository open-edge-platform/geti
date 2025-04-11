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

import { useEffect, useReducer, useRef } from 'react';

import { TextField } from '@adobe/react-spectrum';
import { SpectrumTextFieldProps, TextFieldRef } from '@react-types/textfield';

import { useEventListener } from '../../../../../../hooks/event-listener/event-listener.hook';
import { KeyboardEvents } from '../../../../../keyboard-events/keyboard.interface';
import { HotkeyEditionFieldState } from './hotkey-edition-field.interface';
import { HOTKEY_EDITION_ACTION } from './reducer/actions';
import { reducer } from './reducer/reducer';
import { getKeyBoardKey, isModifierKey } from './utils';

interface HotkeyEditionFieldProps {
    value: string;
    onChange: (value: string) => void;
}

const initialState: HotkeyEditionFieldState = {
    isFocused: false,
    isDirty: true,
    keys: '',
};

export const HotkeyEditionField = ({
    value,
    onChange,
    ...props
}: HotkeyEditionFieldProps & SpectrumTextFieldProps): JSX.Element => {
    const [state, dispatch] = useReducer(reducer, initialState);
    const textFieldRef = useRef<TextFieldRef>(null);
    const hotKeysPressed = useRef<string[]>([]);

    useEffect(() => {
        textFieldRef.current?.focus();
    }, []);

    const onFocusChange = (isFocused: boolean) => {
        dispatch({ type: HOTKEY_EDITION_ACTION.CHANGE_FOCUS, isFocused });

        props.onFocusChange && props.onFocusChange(isFocused);
    };

    useEventListener(KeyboardEvents.KeyDown, (event: KeyboardEvent) => {
        const { repeat } = event;
        const newKey = getKeyBoardKey(event);

        const [currentKey] = hotKeysPressed.current;
        const hasMultipleModifiers = isModifierKey(currentKey) && isModifierKey(newKey);

        if (state.isFocused && !repeat && !hasMultipleModifiers) {
            hotKeysPressed.current.push(newKey);
            event.preventDefault();
        }
    });

    useEventListener(KeyboardEvents.KeyUp, (event: KeyboardEvent) => {
        if (state.isFocused) {
            dispatch({ type: HOTKEY_EDITION_ACTION.ADD_KEY, keys: hotKeysPressed.current });

            hotKeysPressed.current = [];

            event.preventDefault();
        }
    });

    useEffect(() => {
        state.keys && onChange(state.keys);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [state.keys]);

    return (
        <TextField
            {...props}
            value={value}
            ref={textFieldRef}
            minWidth={'size-1600'}
            placeholder={'Press key(s)'}
            onFocusChange={onFocusChange}
        />
    );
};
