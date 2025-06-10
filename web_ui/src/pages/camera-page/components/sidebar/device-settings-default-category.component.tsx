// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Disclosure, DisclosurePanel, DisclosureTitle } from '@geti/ui';

import { DeviceConfiguration } from '../../providers/util';
import { settingsMetadata } from './device-settings-metadata';
import { SettingOption } from './setting-option.component';

import classes from './device-settings.module.css'; //TODO: Disclosure -> component???

interface DeviceSettingsDefaultCategoryProps {
    deviceConfig: DeviceConfiguration[];
}

export const DeviceSettingsDefaultCategory = ({ deviceConfig }: DeviceSettingsDefaultCategoryProps): JSX.Element => {
    const { categories, defaultCategory } = settingsMetadata;

    const settingsMetadataFieldsKeys = categories.reduce(
        (list: string[], category) => [...list, ...category.attributesKeys],
        []
    );

    const defaultCategoryAttributesKeys = deviceConfig?.filter(
        ({ name }) => !settingsMetadataFieldsKeys.includes(name)
    );

    return (
        <Disclosure isHidden={!defaultCategoryAttributesKeys.length}>
            <DisclosureTitle UNSAFE_className={classes.sectionHeader}>{defaultCategory}</DisclosureTitle>
            <DisclosurePanel>
                {defaultCategoryAttributesKeys.map(({ name, config, onChange }) => (
                    <SettingOption key={name} label={name} config={config} onChange={onChange} />
                ))}
            </DisclosurePanel>
        </Disclosure>
    );
};
