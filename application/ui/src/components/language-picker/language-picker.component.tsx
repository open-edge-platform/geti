// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SUPPORTED_LANGUAGES, useTranslation } from '@/i18n';
import { Item, Key, Picker, Text } from '@geti-ui/ui';

import cnFlag from '../../assets/flags/cn.svg?url';
import esFlag from '../../assets/flags/es.svg?url';
import itFlag from '../../assets/flags/it.svg?url';
import ptFlag from '../../assets/flags/pt.svg?url';
import usFlag from '../../assets/flags/us.svg?url';

import classes from './language-picker.module.scss';

// Image files, not emoji: Windows/WebView2 renders regional-indicator flag emojis as letters.
const LANGUAGE_FLAGS: Partial<Record<string, string>> = {
    en: usFlag,
    es: esFlag,
    it: itFlag,
    pt: ptFlag,
    'zh-CN': cnFlag,
};

const getLanguageName = (language: string): string =>
    new Intl.DisplayNames([language], { type: 'language' }).of(language) ?? language;

const languages = SUPPORTED_LANGUAGES.map((language) => ({
    id: language,
    code: language.toUpperCase(),
    name: getLanguageName(language),
    flag: LANGUAGE_FLAGS[language],
}));

export const LanguagePicker = () => {
    const { i18n } = useTranslation();

    const handleChange = (key: Key | null) => {
        if (key !== null) void i18n.changeLanguage(String(key));
    };

    return (
        <Picker
            aria-label={'Change language'}
            items={languages}
            selectedKey={i18n.resolvedLanguage ?? i18n.language}
            onSelectionChange={handleChange}
            isQuiet
        >
            {({ id, code, name, flag }) => (
                <Item key={id} textValue={name}>
                    <Text>
                        <span className={classes.option}>
                            {flag !== undefined && <img src={flag} alt={name} className={classes.flag} />}
                            {code}
                        </span>
                    </Text>
                </Item>
            )}
        </Picker>
    );
};
