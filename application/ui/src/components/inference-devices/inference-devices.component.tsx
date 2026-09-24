// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Key } from 'react';

import { $api } from '@/api';
import type { DeviceInfo } from '@/api/types';
import { Item, Picker } from '@geti-ui/ui';

// Generate device id based on type and index (if available) to ensure uniqueness
// in case of multiple devices of the same type (e.g., multiple GPUs)
const getDeviceId = (device: DeviceInfo): string =>
    device.index != null ? `${device.type}-${device.index}` : device.type;

type InferenceDevicesProps = {
    selectedKey: string;
    onSelectionChange: (selectedKey: string) => void;
    isQuiet?: boolean;
    isDisabled?: boolean;
    label: string;
    maxWidth?: string;
    width?: string;
};

export const InferenceDevices = ({
    selectedKey,
    onSelectionChange,
    isDisabled = false,
    isQuiet = false,
    label,
    maxWidth,
    width = '100%',
}: InferenceDevicesProps) => {
    const { data: devices } = $api.useSuspenseQuery('get', '/api/system/devices/inference');

    const items = devices.map((device) => ({ ...device, id: getDeviceId(device) }));

    const handleSelectionChange = (key: Key | null): void => {
        if (key === null || key === selectedKey) {
            return;
        }

        onSelectionChange(key.toString());
    };

    return (
        <Picker
            isQuiet={isQuiet}
            maxWidth={maxWidth}
            width={width}
            items={items}
            onSelectionChange={handleSelectionChange}
            selectedKey={selectedKey}
            isDisabled={isDisabled}
            label={label}
        >
            {(device) => <Item key={device.id}>{device.name}</Item>}
        </Picker>
    );
};
