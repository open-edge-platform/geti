// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Fragment } from 'react';

import { RequiredTextField } from '@/components/required-text-field/required-text-field.component';
import { useTranslation } from '@/i18n';
import { ActionButton, Content, ContextualHelp, Flex, Grid, Text, TextField } from '@geti-ui/ui';
import { Add, Delete } from '@geti-ui/ui/icons';

import { getDuplicateKeyIndexes, type HeaderRow } from './utils';

import classes from './header-key-value-builder.module.scss';

type HeaderKeyValueBuilderProps = {
    value: HeaderRow[];
    onChange: (value: HeaderRow[]) => void;
};

const KEYS_LABEL = 'headers-keys';
const VALUES_LABEL = 'headers-values';

export const HeaderKeyValueBuilder = ({ value, onChange }: HeaderKeyValueBuilderProps) => {
    const { t } = useTranslation();
    const title = t('inference.sinks.fields.headers');
    const duplicateKeyIndexes = getDuplicateKeyIndexes(value);

    const addRow = () => onChange([...value, { key: '', value: '' }]);

    const updateRow = (indexToUpdate: number, patch: Partial<HeaderRow>) =>
        onChange(value.map((row, index) => (index === indexToUpdate ? { ...row, ...patch } : row)));

    const removeRow = (indexToRemove: number) => onChange(value.filter((_, index) => index !== indexToRemove));

    return (
        <Flex direction='column' gap='size-100'>
            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <Flex gap={'size-100'}>
                    <Text UNSAFE_className={classes.title}>{title}</Text>

                    <ContextualHelp variant='info'>
                        <Content>
                            <Text>{t('inference.sinks.webhook.headersHelp', { title })}</Text>
                        </Content>
                    </ContextualHelp>
                </Flex>
                <ActionButton isQuiet aria-label='Add header' onPress={addRow}>
                    <Add />
                </ActionButton>
            </Flex>

            <Grid columns={['1fr', '1fr', '50px']} gap={'size-100'}>
                {value.map((row, index) => {
                    const isDuplicate = duplicateKeyIndexes.has(index);

                    return (
                        <Fragment key={index}>
                            <TextField
                                isQuiet
                                isRequired
                                width={'100%'}
                                value={row.key}
                                aria-label={KEYS_LABEL}
                                placeholder={t('inference.sinks.webhook.keyPlaceholder')}
                                validationState={isDuplicate ? 'invalid' : undefined}
                                errorMessage={
                                    isDuplicate
                                        ? t('inference.validation.keyDuplicate')
                                        : t('inference.validation.keyEmpty')
                                }
                                onChange={(key) => updateRow(index, { key })}
                            />
                            <RequiredTextField
                                isQuiet
                                width={'100%'}
                                value={row.value}
                                aria-label={VALUES_LABEL}
                                placeholder={t('inference.sinks.webhook.valuePlaceholder')}
                                errorMessage={t('inference.validation.valueEmpty')}
                                isDisabled={row.key === ''}
                                onChange={(next) => updateRow(index, { value: next })}
                            />
                            <ActionButton isQuiet aria-label='Remove' onPress={() => removeRow(index)}>
                                <Delete />
                            </ActionButton>
                        </Fragment>
                    );
                })}
            </Grid>
        </Flex>
    );
};
