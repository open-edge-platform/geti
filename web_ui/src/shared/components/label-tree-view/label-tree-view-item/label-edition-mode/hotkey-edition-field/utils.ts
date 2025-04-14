// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getKeyName } from '../../../../../hotkeys';
import { KeyMap } from '../../../../../keyboard-events/keyboard.interface';

export const isModifierKey = (key = ''): boolean => {
    return [
        KeyMap.Alt.toLocaleUpperCase(),
        KeyMap.Meta.toLocaleUpperCase(),
        KeyMap.Command.toLocaleUpperCase(),
        KeyMap.Shift.toLocaleUpperCase(),
        KeyMap.Control.toLocaleUpperCase(),
    ].includes(key.toLocaleUpperCase());
};

export const getKeyBoardKey = (event: KeyboardEvent) => {
    const { key, code, shiftKey } = event;

    if (shiftKey && code.includes('Digit')) {
        return code[code.length - 1];
    }

    return getKeyName(key);
};
