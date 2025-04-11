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

import { useHotkeys } from 'react-hotkeys-hook';

import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../utils';

export const useToggleSelectAllKeyboardShortcut = (toggleSelectAll: (isSelected: boolean) => void): void => {
    const { hotkeys } = useAnnotatorHotkeys();

    useHotkeys(
        hotkeys.selectAll,
        (event) => {
            event.preventDefault();

            toggleSelectAll(true);
        },
        HOTKEY_OPTIONS,
        [toggleSelectAll]
    );

    useHotkeys(
        hotkeys.deselectAll,
        (event) => {
            event.preventDefault();

            toggleSelectAll(false);
        },
        HOTKEY_OPTIONS,
        [toggleSelectAll]
    );
};
