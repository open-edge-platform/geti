// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useHotkeys } from 'react-hotkeys-hook';

import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../utils';

export const useSaveAnnotationsKeyboardShortcut = (submit: () => void, canSave: boolean): void => {
    const { hotkeys } = useAnnotatorHotkeys();

    useHotkeys(
        hotkeys.saveAnnotations,
        (event) => {
            event.preventDefault();

            if (canSave) {
                submit();
            }
        },
        HOTKEY_OPTIONS,
        [canSave, submit]
    );
};
