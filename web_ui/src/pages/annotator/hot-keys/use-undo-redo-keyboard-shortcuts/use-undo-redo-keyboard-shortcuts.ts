// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useHotkeys } from 'react-hotkeys-hook';

import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../utils';

export const useUndoRedoKeyboardShortcuts = (
    action: 'undo' | 'redo' | 'redoSecond',
    enabled: boolean,
    onSelect: () => void
): void => {
    const { hotkeys } = useAnnotatorHotkeys();

    useHotkeys(hotkeys[action], onSelect, { ...HOTKEY_OPTIONS, enabled }, [onSelect]);
};
