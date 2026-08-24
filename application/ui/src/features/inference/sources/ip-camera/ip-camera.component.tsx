// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig } from '@/api/types';
import { Flex, Switch, TextField } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

type IpCameraProps = {
    defaultState?: IPCameraSourceConfig;
};

export const IpCamera = ({ defaultState }: IpCameraProps) => {
    const { t } = useTranslation();

    return (
        <Flex direction='column' gap='size-200'>
            <TextField isHidden label='id' name='id' defaultValue={defaultState?.id} />
            <TextField width={'100%'} label={t('inference.nameLabel')} name='name' defaultValue={defaultState?.name} />
            <TextField
                isRequired
                width={'100%'}
                label={t('inference.streamUrlLabel')}
                name='stream_url'
                defaultValue={defaultState?.stream_url}
            />
            <Switch
                name='auth_required'
                aria-label={t('inference.requireAuthAriaLabel')}
                defaultSelected={defaultState?.auth_required}
                key={defaultState?.auth_required ? 'true' : 'false'}
            >
                {t('inference.requireAuthentication')}
            </Switch>
        </Flex>
    );
};
