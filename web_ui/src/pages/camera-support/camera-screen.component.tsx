// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CameraPage } from '../camera-page/camera-page.component';
import { DeviceSettingsProvider } from '../camera-page/providers/device-settings-provider.component';

export const CameraScreen = () => {
    return (
        <DeviceSettingsProvider>
            <CameraPage />
        </DeviceSettingsProvider>
    );
};
