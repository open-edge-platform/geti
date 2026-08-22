// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from 'react-i18next';

import { i18n, resources } from './config';

export { i18n, LANGUAGE_STORAGE_KEY, resources } from './config';

export type SupportedLanguage = keyof typeof resources & string;

interface LanguageOption {
    readonly code: SupportedLanguage;
    readonly label: string;
}

export const SUPPORTED_LANGUAGES: readonly LanguageOption[] = [
    { code: 'en', label: 'English' },
    { code: 'zh-CN', label: '中文' },
];

/**
 * Changes the application language and persists the choice. Subsequent
 * sessions start with the persisted language instead of the browser default.
 */
export const changeLanguage = async (language: SupportedLanguage): Promise<void> => {
    await i18n.changeLanguage(language);
};

/** Returns the active language together with `changeLanguage`, re-rendering on language changes. */
export const useLanguage = (): { language: string; changeLanguage: typeof changeLanguage } => {
    const { i18n: instance } = useTranslation();

    return { language: instance.language, changeLanguage };
};
