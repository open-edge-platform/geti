// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Resource } from 'i18next';

import en from './locales/en.json';
import it from './locales/it.json';
import pt from './locales/pt.json';
import zhCN from './locales/zh-CN.json';

export const DEFAULT_LANGUAGE = 'en';

export const resources: Resource = {
    [DEFAULT_LANGUAGE]: { translation: en },
    it: { translation: it },
    pt: { translation: pt },
    'zh-CN': { translation: zhCN },
};

export const SUPPORTED_LANGUAGES = Object.keys(resources);
