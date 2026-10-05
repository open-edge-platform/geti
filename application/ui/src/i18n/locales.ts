// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Resource } from 'i18next';

import en from './locales/en.json';
import es from './locales/es.json';
import it from './locales/it.json';
import pl from './locales/pl.json';
import pt from './locales/pt.json';
import zhCN from './locales/zh-CN.json';

export const DEFAULT_LANGUAGE = 'en';
type Catalog = typeof en;

export const resources: Resource = {
    [DEFAULT_LANGUAGE]: { translation: en },
    es: { translation: es satisfies Catalog },
    it: { translation: it satisfies Catalog },
    pl: { translation: pl satisfies Catalog },
    pt: { translation: pt satisfies Catalog },
    'zh-CN': { translation: zhCN satisfies Catalog },
};

export const SUPPORTED_LANGUAGES = Object.keys(resources);
