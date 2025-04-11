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

import { Label } from '../../../../core/labels/label.interface';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { HOTKEY_OPTIONS } from '../utils';

interface UseLabelsKeyboardShortcut {
    label: Required<Label>;
    hotkeyHandler: () => void;
    annotationToolContext: AnnotationToolContext;
}

export const useLabelsKeyboardShortcut = ({ label, hotkeyHandler }: UseLabelsKeyboardShortcut): void => {
    useHotkeys(
        label.hotkey,
        (event) => {
            event.preventDefault();

            hotkeyHandler();
        },
        HOTKEY_OPTIONS
    );
};
