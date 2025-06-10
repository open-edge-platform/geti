// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface DeviceSettingsCategory {
    categoryName: string;
    attributesKeys: string[];
}

export interface DeviceSettingsDependency {
    key: string;
    type: 'selection';
    children: string[];
}

export interface DeviceSettingsMetadata {
    categories: DeviceSettingsCategory[];
    defaultCategory: string;
    dependencies: DeviceSettingsDependency[];
}
