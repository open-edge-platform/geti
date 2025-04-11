// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Heading, Item, Key, Picker, View } from '@adobe/react-spectrum';
import orderBy from 'lodash/orderBy';

import { Divider } from '../../../../shared/components/divider/divider.component';
import { useDeviceSettings } from '../../providers/device-settings-provider.component';
import { applySettings } from '../../providers/util';
import { SettingOption } from './setting-option.component';

export const DeviceSettings = () => {
    const { webcamRef, videoDevices, selectedDeviceId, deviceConfig, setSelectedDeviceId } = useDeviceSettings();
    const sortedByOptions = orderBy(deviceConfig, ['config.options'], 'desc');

    return (
        <View position={'relative'}>
            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <Heading level={3}>Camera Settings</Heading>
            </Flex>

            <Picker
                width={'100%'}
                label={'Device'}
                items={videoDevices}
                aria-label={'devices'}
                selectedKey={selectedDeviceId}
                placeholder={'Integrated Camera'}
                onSelectionChange={(key: Key) => setSelectedDeviceId(String(key))}
            >
                {({ deviceId, label }) => <Item key={deviceId}>{label}</Item>}
            </Picker>

            <Divider size={'S'} marginTop={'size-250'} marginBottom={'size-250'} />

            {sortedByOptions.map(({ name, config }) => (
                <SettingOption
                    key={name}
                    label={name}
                    config={config}
                    onChange={(value) => {
                        if (webcamRef.current?.stream) {
                            applySettings(webcamRef.current?.stream, { [name]: value });
                        }
                    }}
                />
            ))}
        </View>
    );
};
