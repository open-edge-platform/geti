// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useId, useRef } from 'react';

import { SUPPORTED_LANGUAGES, useTranslation } from '@/i18n';
import {
    ActionButton,
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    Key,
    Radio,
    RadioGroup,
    Text,
    Tooltip,
    TooltipTrigger,
} from '@geti-ui/ui';
import { Gear } from '@geti-ui/ui/icons';
import { capitalize } from 'lodash-es';

import { version } from '../../../package.json';

import classes from './preferences.module.scss';

const MAX_VISIBLE_ROWS = 8;
const ROW_HEIGHT_PX = 32;

const getLanguageName = (language: string): string =>
    new Intl.DisplayNames([language], { type: 'language' }).of(language) ?? language;

const languages = SUPPORTED_LANGUAGES.map((language) => ({
    id: language,
    name: getLanguageName(language),
}));

const LanguageList = ({ labelId }: { labelId: string }) => {
    const { i18n } = useTranslation();
    const current = i18n.resolvedLanguage ?? i18n.language;
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        scrollRef.current?.querySelector('input:checked')?.scrollIntoView({ block: 'nearest' });
    }, []);

    const handleChange = (key: Key) => {
        void i18n.changeLanguage(String(key));
    };

    return (
        <div ref={scrollRef} className={classes.languageScroll} style={{ maxHeight: MAX_VISIBLE_ROWS * ROW_HEIGHT_PX }}>
            <RadioGroup aria-labelledby={labelId} value={current} onChange={handleChange}>
                {languages.map(({ id, name }) => (
                    <Radio key={id} value={id}>
                        <Text>{capitalize(name)}</Text>
                    </Radio>
                ))}
            </RadioGroup>
        </div>
    );
};

const LanguagePreferences = () => {
    const { t } = useTranslation();
    const labelId = useId();

    return (
        <Flex direction={'column'} gap={'size-100'}>
            <Text id={labelId}>{t('common.labels.language')}</Text>
            <LanguageList labelId={labelId} />
        </Flex>
    );
};

export const Preferences = () => {
    const { t } = useTranslation();

    return (
        <DialogTrigger type={'popover'} placement={'bottom end'} hideArrow>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton isQuiet aria-label={'Preferences'}>
                    <Gear />
                </ActionButton>
                <Tooltip>{t('navigation.preferences')}</Tooltip>
            </TooltipTrigger>
            <Dialog width={'size-4600'}>
                <Heading>{t('navigation.preferences')}</Heading>
                <Divider size={'S'} />
                <Content>
                    <Flex direction={'column'} gap={'size-200'}>
                        <LanguagePreferences />
                        <Text UNSAFE_className={classes.version}>Geti v{version}</Text>
                    </Flex>
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
