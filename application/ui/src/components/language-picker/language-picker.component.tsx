// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SUPPORTED_LANGUAGES, useTranslation } from '@/i18n';
import { Item, Key, Picker, Text } from '@geti-ui/ui';

import classes from './language-picker.module.scss';

const getLanguageName = (language: string): string =>
    new Intl.DisplayNames([language], { type: 'language' }).of(language) ?? language;

export const languages = SUPPORTED_LANGUAGES.map((language) => ({
    id: language,
    code: language.toUpperCase(),
    name: getLanguageName(language),
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
            {({ id, code, name }) => (
                <Item key={id} textValue={name}>
                    <Text>
                        <span className={classes.option}>{code}</span>
                    </Text>
                </Item>
            )}
        </Picker>
    );
};
