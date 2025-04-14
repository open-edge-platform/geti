// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
