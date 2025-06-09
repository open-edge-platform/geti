// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Disclosure, DisclosurePanel, DisclosureTitle, Flex, Heading, Item, Key, Picker, View } from '@geti/ui';

import { useDeviceSettings } from '../../providers/device-settings-provider.component';
import { checkIfDisplaySetting } from '../../providers/util';
import { DeviceSettingsDefaultCategory } from './device-settings-default-category.component';
import { settingsMetadata } from './device-settings-metadata';
import { SettingOption } from './setting-option.component';

import classes from './device-settings.module.css';

const Header = ({ text }: { text: string }) => (
    <Flex alignItems={'center'} justifyContent={'space-between'}>
        <Heading level={3}>{text}</Heading>
    </Flex>
);

//TODO:
//fixbug dependencies - changed
//show after the standup!
//add tests!

export const DeviceSettings = () => {
    const { categories, dependencies } = settingsMetadata;

    const { videoDevices, selectedDeviceId, deviceConfig, setSelectedDeviceId } = useDeviceSettings();

    return (
        <View position={'relative'}>
            <Header text={'Camera Settings'} />

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

            {categories.map(({ categoryName, attributesKeys }) => (
                <Disclosure key={categoryName}>
                    <DisclosureTitle UNSAFE_className={classes.sectionHeader}>{categoryName}</DisclosureTitle>
                    <DisclosurePanel>
                        {attributesKeys.map((key) => {
                            const currentOption = deviceConfig.find((option) => option.name === key);
                            if (currentOption) {
                                const shouldDisplay = checkIfDisplaySetting(currentOption, deviceConfig, dependencies);
                                const { name, config, onChange } = currentOption;

                                return (
                                    shouldDisplay && (
                                        <SettingOption key={name} label={name} config={config} onChange={onChange} />
                                    )
                                );
                            }
                        })}
                    </DisclosurePanel>
                </Disclosure>
            ))}

            <DeviceSettingsDefaultCategory deviceConfig={deviceConfig} />
        </View>
    );
};
