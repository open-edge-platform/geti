// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { i18n } from '../../i18n';

export const validateProjectName = (name: string, projectNames: string[]): string | undefined => {
    if (name.trim().length === 0) {
        return i18n.t('validation.emptyProjectName');
    }

    if (projectNames.includes(name)) {
        return i18n.t('validation.duplicateProjectName');
    }

    return undefined;
};

export const PROJECT_NAME_MAX_LENGTH = 100;
