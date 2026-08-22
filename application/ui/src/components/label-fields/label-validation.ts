// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Label } from '@/api/types';

import { i18n } from '../../i18n';
import { convertHotkeyToOSFormat } from '../../shared/hotkeys-definition';

export const validateLabelName = (name: string, existingLabels: Label[], excludeId?: string): string | undefined => {
    const trimmedName = name.trim();

    const isDuplicate = existingLabels.some((label) => label.name === trimmedName && label.id !== excludeId);

    if (isDuplicate) {
        return i18n.t('validation.duplicateLabelName');
    }

    return undefined;
};

export const validateLabelHotkey = (hotkey: string, allHotkeys: string[]): string | undefined => {
    const osFormatHotkeys = allHotkeys.map(convertHotkeyToOSFormat).map((key) => key.toLowerCase());

    if (osFormatHotkeys.includes(hotkey.toLowerCase())) {
        return i18n.t('validation.hotkeyInUse');
    }

    return undefined;
};
