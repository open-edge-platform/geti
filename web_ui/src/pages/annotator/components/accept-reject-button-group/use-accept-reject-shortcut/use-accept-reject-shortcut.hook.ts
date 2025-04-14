// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
