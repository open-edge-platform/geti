// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Key } from 'react';

import { $api } from '@/api';
import { useTranslation } from '@/i18n';
import { ActionButton, Flex, Item, Loading, Picker, TextField } from '@geti-ui/ui';
import { Refresh } from '@geti-ui/ui/icons';

import type { UsbCameraFormState } from './utils';

interface UsbCameraFieldsProps {
    value: UsbCameraFormState;
    onChange: (next: UsbCameraFormState) => void;
}

export const UsbCameraFields = ({ value, onChange }: UsbCameraFieldsProps) => {
    const { t } = useTranslation();

    const {
        data: cameraDevices = [],
        isLoading,
        isRefetching,
        refetch,
    } = $api.useQuery('get', '/api/system/devices/camera');

    const handleSelectionChange = (key: Key | null) => {
        if (key === null) return;

        onChange({ ...value, device_id: Number(key) });
    };

    return (
        <Flex direction='column' gap='size-200'>
            <TextField
                width='100%'
                label={t('common.labels.name')}
                value={value.name}
                onChange={(name) => onChange({ ...value, name })}
            />

            <Flex alignItems='end' gap='size-200'>
                <Picker
                    flex='1'
                    isRequired
                    label={t('inference.sources.fields.camera')}
                    items={cameraDevices.map(({ index, name }) => ({ id: index, name }))}
                    isLoading={isLoading}
                    aria-label='Camera list'
                    selectedKey={value.device_id === null ? null : String(value.device_id)}
                    onSelectionChange={handleSelectionChange}
                >
                    {(item) => <Item key={item.id}>{item.name}</Item>}
                </Picker>

                <ActionButton
                    isQuiet
                    onPress={() => refetch()}
                    aria-label='Refresh Cameras'
                    isDisabled={isLoading || isRefetching}
                >
                    {isRefetching ? <Loading mode={'inline'} size='S' /> : <Refresh />}
                </ActionButton>
            </Flex>
        </Flex>
    );
};
