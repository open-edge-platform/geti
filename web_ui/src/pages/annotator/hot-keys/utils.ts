// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Options } from 'react-hotkeys-hook';

export const HOTKEY_OPTIONS: Options = {
    enableOnFormTags: ['SELECT', 'INPUT'],
    // We want to disable any hotkeys when the user is typing into an input form,
    // otherwise pressing "backspace" could accidentally remove annotations.
    // This filter will try to do this, but may not be perfect.
    preventDefault: false,
    ignoreEventWhen: (event) => {
        // @ts-expect-error this won't fail if type does not exist
        return event.target?.type === 'text';
    },
};
