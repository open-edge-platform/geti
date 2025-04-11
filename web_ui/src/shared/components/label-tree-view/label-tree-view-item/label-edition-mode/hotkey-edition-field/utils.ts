// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
