// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createInstance, type i18n as I18n } from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import zhCN from './locales/zh-CN.json';
import zhHK from './locales/zh-HK.json';
import zhMO from './locales/zh-MO.json';
import zhTW from './locales/zh-TW.json';

export const resources = {
    en: { translation: en },
    'zh-CN': { translation: zhCN },
    'zh-HK': { translation: zhHK },
    'zh-MO': { translation: zhMO },
    'zh-TW': { translation: zhTW },
} as const;

export const LANGUAGE_STORAGE_KEY = 'geti-language';

/** Maps any detected `zh*` language tag to one of the supported Chinese locales. */
const normalizeChineseLanguage = (language: string): string => {
    const lower = language.toLowerCase();
    if (/^zh-(hant|tw|hk|mo)/.test(lower)) {
        if (lower.startsWith('zh-hk')) return 'zh-HK';
        if (lower.startsWith('zh-mo')) return 'zh-MO';
        return 'zh-TW';
    }
    return 'zh-CN';
};

const i18next = createInstance();

if (!i18next.isInitialized) {
    void i18next
        .use(LanguageDetector)
        .use(initReactI18next)
        .init({
            resources,
            fallbackLng: {
                'zh-MO': ['zh-HK'],
                'zh-HK': ['zh-TW'],
                default: ['en'],
            },
            supportedLngs: ['en', 'zh-CN', 'zh-TW', 'zh-HK', 'zh-MO'],
            detection: {
                order: ['localStorage', 'navigator'],
                lookupLocalStorage: LANGUAGE_STORAGE_KEY,
                caches: ['localStorage'],
                convertDetectedLanguage: (language) =>
                    language.toLowerCase().startsWith('zh') ? normalizeChineseLanguage(language) : language,
            },
            interpolation: { escapeValue: false },
            react: { useSuspense: false },
        });
}

export const i18n: I18n = i18next;
