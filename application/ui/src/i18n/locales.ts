// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Resource } from 'i18next';

import en from './locales/en.json';
import es from './locales/es.json';
import it from './locales/it.json';
import pt from './locales/pt.json';
import zhCN from './locales/zh-CN.json';
import zhHK from './locales/zh-HK.json';
import zhMO from './locales/zh-MO.json';
import zhTW from './locales/zh-TW.json';

export const DEFAULT_LANGUAGE = 'en';

export const resources: Resource = {
    [DEFAULT_LANGUAGE]: { translation: en },
    es: { translation: es },
    it: { translation: it },
    pt: { translation: pt },
    'zh-CN': { translation: zhCN },
    'zh-HK': { translation: zhHK },
    'zh-MO': { translation: zhMO },
    'zh-TW': { translation: zhTW },
};

export const SUPPORTED_LANGUAGES = Object.keys(resources);
