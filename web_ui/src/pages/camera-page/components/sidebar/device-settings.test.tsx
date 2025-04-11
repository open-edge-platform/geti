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

import { defaultTheme, Provider as ThemeProvider } from '@adobe/react-spectrum';
import { fireEvent, render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { SettingsContextProps, useDeviceSettings } from '../../providers/device-settings-provider.component';
import { applySettings } from '../../providers/util';
import { getUseCameraSettings } from '../../test-utils/camera-setting';
import { DeviceSettings } from './device-settings.component';

jest.mock('../../providers/util', () => ({
    applySettings: jest.fn(),
}));

jest.mock('../../providers/device-settings-provider.component', () => ({
    useDeviceSettings: jest.fn(),
}));

const getMockedDevice = (number: number) =>
    ({
        kind: 'videoinput',
        label: `camera-${number}`,
        groupId: `groupId-${number}`,
        deviceId: `deviceId-${number}`,
    }) as MediaDeviceInfo;

describe('Settings', () => {
    const renderApp = (config: Partial<SettingsContextProps & { stream: unknown }> = {}) => {
        jest.mocked(useDeviceSettings).mockReturnValue(getUseCameraSettings(config));

        render(
            <ThemeProvider theme={defaultTheme}>
                <DeviceSettings />
            </ThemeProvider>
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('update selected device id', async () => {
        const cameraOne = getMockedDevice(1);
        const cameraTwo = getMockedDevice(2);
        const videoDevices = [cameraOne, cameraTwo];
        const mockedSetSelectedDeviceId = jest.fn();

        renderApp({ videoDevices, setSelectedDeviceId: mockedSetSelectedDeviceId });

        fireEvent.click(screen.getByLabelText('devices'));

        await userEvent.selectOptions(
            screen.getByRole('listbox'),
            screen.getByRole('option', { name: cameraTwo.label })
        );

        expect(mockedSetSelectedDeviceId).toHaveBeenCalledWith(cameraTwo.deviceId);
    });

    it('apply settings', () => {
        const mockedStream = {} as MediaStream;
        const mockedDeviceConfig = {
            name: 'frameRate',
            config: { type: 'minMax' as const, value: 0, max: 30, min: 0 },
        };

        renderApp({ deviceConfig: [mockedDeviceConfig], stream: mockedStream });

        fireEvent.keyDown(screen.getByRole('slider'), { key: 'Right' });

        expect(applySettings).toHaveBeenCalledWith(mockedStream, {
            [mockedDeviceConfig.name]: `${mockedDeviceConfig.config.value + 1}`,
        });
    });
});
