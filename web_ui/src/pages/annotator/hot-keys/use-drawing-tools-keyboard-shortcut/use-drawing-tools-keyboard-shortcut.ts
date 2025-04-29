// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
