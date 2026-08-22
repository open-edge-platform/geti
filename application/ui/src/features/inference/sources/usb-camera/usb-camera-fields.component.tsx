// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Key, useRef, useState } from 'react';

import { $api } from '@/api';
import type { USBCameraSourceConfig } from '@/api/types';
import { ActionButton, Flex, Item, Loading, Picker, TextField } from '@geti-ui/ui';
import { Refresh } from '@geti-ui/ui/icons';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

type UsbCameraProps = {
    defaultState?: USBCameraSourceConfig;
};

export const UsbCamera = ({ defaultState }: UsbCameraProps) => {
    const { t } = useTranslation();

    const [name, setName] = useState(defaultState?.name);
    const isSystemName = useRef(isEmpty(defaultState?.name));

    const {
        data: cameraDevices,
        isLoading,
        isRefetching,
        refetch,
    } = $api.useQuery('get', '/api/system/devices/camera');

    const devices = (cameraDevices ?? []).map((device) => ({
        id: device.index,
        name: device.name,
    }));

    const handleNameChange = (value: string) => {
        setName(value);
        isSystemName.current = false;
    };

    const handleSelectionChange = (key: Key | null) => {
        const device = devices.find(({ id }) => id === Number(key));

        if (device && isSystemName.current) {
            setName(device.name);
        }
    };

    return (
        <Flex direction='column' gap='size-200'>
            <TextField isHidden label='id' name='id' defaultValue={defaultState?.id} />
            <TextField isHidden label='name' name='name' value={name} />
            <TextField
                width='100%'
                label={t('inference.nameLabel')}
                name='name_display'
                value={name}
                onChange={handleNameChange}
            />

            <Flex alignItems='end' gap='size-200'>
                <Picker
                    flex='1'
                    isRequired
                    label={t('inference.cameraLabel')}
                    name='device_id'
                    items={devices}
                    isLoading={isLoading}
                    aria-label={t('inference.cameraListAriaLabel')}
                    defaultSelectedKey={String(defaultState?.device_id)}
                    onSelectionChange={handleSelectionChange}
                >
                    {(item) => <Item key={item.id}>{item.name}</Item>}
                </Picker>

                <ActionButton
                    isQuiet
                    onPress={() => refetch()}
                    aria-label={t('inference.refreshCamerasAriaLabel')}
                    isDisabled={isLoading || isRefetching}
                >
                    {isRefetching ? <Loading mode={'inline'} size='S' /> : <Refresh />}
                </ActionButton>
            </Flex>
        </Flex>
    );
};
