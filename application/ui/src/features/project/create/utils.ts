// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { TranslateFn } from '@/i18n';

// Generates the first default name that is not taken, comparing rendered names instead of
// parsing them, so it stays correct in any locale.
export const generateUniqueProjectName = (existingNames: string[], t: TranslateFn): string => {
    const takenNames = new Set(existingNames);

    let number = 1;
    let candidate = t('project.create.defaultName', { number });

    while (takenNames.has(candidate)) {
        number += 1;
        candidate = t('project.create.defaultName', { number });
    }

    return candidate;
};
