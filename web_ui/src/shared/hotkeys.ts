// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isMac } from '@react-aria/utils';

// Get hotkey name based on user's OS
export const getKeyName = (key: string): string => {
    const lowerCaseKey = key.toLowerCase();

    if (lowerCaseKey.includes(CTRL_KEY_DESCRIPTION)) {
        return lowerCaseKey.replace(CTRL_KEY_DESCRIPTION, CTRL_KEY).toLocaleUpperCase();
    }

    if (lowerCaseKey.includes(COMMAND_KEY)) {
        return lowerCaseKey.replace(COMMAND_KEY, COMMAND_KEY_DESCRIPTION).toLocaleUpperCase();
    }

    return key.toLocaleUpperCase();
};

const CTRL_KEY = 'ctrl';
const CTRL_KEY_DESCRIPTION = 'control';
const COMMAND_KEY = 'meta';
const COMMAND_KEY_DESCRIPTION = 'cmd';

export const CTRL_OR_COMMAND_KEY = isMac() ? COMMAND_KEY : CTRL_KEY;
