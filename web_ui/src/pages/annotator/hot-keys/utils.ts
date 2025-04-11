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
