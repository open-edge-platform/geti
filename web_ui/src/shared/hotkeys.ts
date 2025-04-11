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
