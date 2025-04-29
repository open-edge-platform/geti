// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getKeyName } from '../../../../../../hotkeys';
import { HotkeyEditionFieldState } from '../hotkey-edition-field.interface';
import { Action, HOTKEY_EDITION_ACTION } from './actions';

export const reducer = (state: HotkeyEditionFieldState, action: Action): HotkeyEditionFieldState => {
    //TODO: there is an issue with with hotkeys when there is more keys. If we want more issue should be fixed
    const MAX_KEYS_IN_HOTKEY = 2;

    switch (action.type) {
        case HOTKEY_EDITION_ACTION.CHANGE_FOCUS:
            return {
                isDirty: false,
                isFocused: action.isFocused,
                keys: state.isDirty ? state.keys : '',
            };

        case HOTKEY_EDITION_ACTION.ADD_KEY:
            const keys = action.keys.slice(-MAX_KEYS_IN_HOTKEY).map((key: string) => getKeyName(key));

            if (!keys.length) {
                return state;
            }

            return {
                ...state,
                isDirty: true,
                keys: keys.join('+').toLocaleUpperCase(),
            };
    }
};
