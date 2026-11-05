// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Flex, Switch, TextField } from '@geti-ui/ui';

import type { IpCameraFormState } from './utils';

interface IpCameraFieldsProps<T extends IpCameraFormState> {
    value: T;
    onChange: (next: T) => void;
}

export const IpCameraFields = <T extends IpCameraFormState>({ value, onChange }: IpCameraFieldsProps<T>) => {
    const { t } = useTranslation();

    return (
        <Flex direction='column' gap='size-200'>
            <TextField
                width={'100%'}
                label={t('common.labels.name')}
                value={value.name}
                onChange={(name) => onChange({ ...value, name })}
            />
            <TextField
                isRequired
                width={'100%'}
                label={t('inference.sources.fields.streamUrl')}
                value={value.stream_url}
                onChange={(stream_url) => onChange({ ...value, stream_url })}
            />
            <Switch
                isEmphasized
                aria-label='Require Authentication'
                isSelected={value.auth_required}
                onChange={(auth_required) => onChange({ ...value, auth_required })}
            >
                {t('inference.sources.fields.requireAuthentication')}
            </Switch>
        </Flex>
    );
};
