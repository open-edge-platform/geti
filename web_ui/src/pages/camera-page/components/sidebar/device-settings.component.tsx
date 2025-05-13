// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Heading, Item, Key, Picker, View } from '@adobe/react-spectrum';
import { orderBy } from 'lodash-es';

import { Divider } from '../../../../shared/components/divider/divider.component';
import { useDeviceSettings } from '../../providers/device-settings-provider.component';
import { applySettings } from '../../providers/util';
import { SettingOption } from './setting-option.component';

export const DeviceSettings = () => {
    const { webcamRef, videoDevices, selectedDeviceId, deviceConfig, setSelectedDeviceId, isMirrored, setIsMirrored } =
        useDeviceSettings();
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

            <SettingOption
                label='Mirror camera'
                config={{ type: 'selection', options: ['Off', 'On'], value: isMirrored ? 'On' : 'Off' }}
                onChange={(value) => {
                    setIsMirrored(value == 'On');
                }}
            />

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
