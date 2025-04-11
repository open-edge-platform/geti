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

import { getKeyBoardKey, isModifierKey } from './utils';

describe('hotkey-edition-field utils', () => {
    it('isModifierKey', () => {
        expect(isModifierKey('Alt')).toBe(true);
        expect(isModifierKey('Meta')).toBe(true);
        expect(isModifierKey('Shift')).toBe(true);
        expect(isModifierKey('Ctrl')).toBe(true);
        expect(isModifierKey('1')).toBe(false);
        expect(isModifierKey('A')).toBe(false);
        expect(isModifierKey('ArrowUp')).toBe(false);
    });

    const mockKeyboardEvent = (key: string, code: string, shiftKey = false): KeyboardEvent =>
        ({ key, code, shiftKey }) as unknown as KeyboardEvent;

    it('getKeyBoardKey', () => {
        expect(getKeyBoardKey(mockKeyboardEvent('ArrowUp', 'ArrowUp'))).toBe('ARROWUP');
        expect(getKeyBoardKey(mockKeyboardEvent('d', 'KeyD'))).toBe('D');
        expect(getKeyBoardKey(mockKeyboardEvent('1', 'Digit1', true))).toBe('1');
        expect(getKeyBoardKey(mockKeyboardEvent('2', 'Digit2', true))).toBe('2');
        expect(getKeyBoardKey(mockKeyboardEvent('3', 'Digit3'))).toBe('3');
    });
});
