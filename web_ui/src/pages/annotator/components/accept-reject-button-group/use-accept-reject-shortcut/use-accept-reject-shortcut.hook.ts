// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DependencyList } from 'react';

import { useHotkeys } from 'react-hotkeys-hook';

import { useAnnotatorHotkeys } from '../../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../../../hot-keys/utils';

interface CallbackProps {
    callback: () => void;
    deps?: DependencyList;
    isEnabled: boolean;
}

export const useAcceptRejectShortcut = (accept: CallbackProps, reject: CallbackProps) => {
    const { hotkeys } = useAnnotatorHotkeys();

    useHotkeys(hotkeys.accept, accept.callback, { ...HOTKEY_OPTIONS, enabled: accept.isEnabled }, [
        accept.isEnabled,
        ...(accept.deps ?? []),
    ]);

    useHotkeys(hotkeys.close, reject.callback, { ...HOTKEY_OPTIONS, enabled: reject.isEnabled }, [
        reject.isEnabled,
        ...(reject.deps ?? []),
    ]);
};
