// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type en from './locales/en.json';

declare module 'i18next' {
    interface CustomTypeOptions {
        resources: {
            translation: typeof en;
        };
    }
}
