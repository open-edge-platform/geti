// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useLabelsKeyboardShortcut } from '../../../../hot-keys/use-labels-keyboard-shortcut/use-labels-keyboard-shortcut.hook';

type LabelHotkeyProps = Parameters<typeof useLabelsKeyboardShortcut>[0];

export const LabelHotkey = ({ label, annotationToolContext, hotkeyHandler }: LabelHotkeyProps): JSX.Element => {
    useLabelsKeyboardShortcut({ label, annotationToolContext, hotkeyHandler });

    return <></>;
};
