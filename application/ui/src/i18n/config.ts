// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createInstance, type i18n as I18n } from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import zhCN from './locales/zh-CN.json';

export const resources = {
    en: { translation: en },
    'zh-CN': { translation: zhCN },
} as const;

export const LANGUAGE_STORAGE_KEY = 'geti-language';

const i18next = createInstance();

if (!i18next.isInitialized) {
    void i18next
        .use(LanguageDetector)
        .use(initReactI18next)
        .init({
            resources,
            fallbackLng: 'en',
            supportedLngs: ['en', 'zh-CN'],
            detection: {
                order: ['localStorage', 'navigator'],
                lookupLocalStorage: LANGUAGE_STORAGE_KEY,
                caches: ['localStorage'],
                convertDetectedLanguage: (language) => (language.toLowerCase().startsWith('zh') ? 'zh-CN' : language),
            },
            interpolation: { escapeValue: false },
            react: { useSuspense: false },
        });
}

export const i18n: I18n = i18next;
