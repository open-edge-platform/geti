// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
