// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export type Action =
    | { type: HOTKEY_EDITION_ACTION.ADD_KEY; keys: string[] }
    | { type: HOTKEY_EDITION_ACTION.CHANGE_FOCUS; isFocused: boolean };

export enum HOTKEY_EDITION_ACTION {
    CHANGE_FOCUS,
    ADD_KEY,
}
