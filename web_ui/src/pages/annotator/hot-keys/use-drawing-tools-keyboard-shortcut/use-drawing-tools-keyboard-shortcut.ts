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

import { DefaultToolTypes } from '../../core/annotation-tool-context.interface';
import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../utils';

export const useDrawingToolsKeyboardShortcut = (
    tool: DefaultToolTypes,
    onSelect: () => void,
    isDisabled = false,
    deps?: unknown[]
): void => {
    const { hotkeys } = useAnnotatorHotkeys();

    useHotkeys(hotkeys[tool], onSelect, { ...HOTKEY_OPTIONS, enabled: !isDisabled }, deps ? deps : [onSelect]);
};
