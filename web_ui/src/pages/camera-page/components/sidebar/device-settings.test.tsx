// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defaultTheme, Provider as ThemeProvider } from '@geti/ui';
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

    it('Allows to mirror the camera feed', async () => {
        const setIsMirrored = jest.fn();

        renderApp({ setIsMirrored });

        fireEvent.click(screen.getByRole('button', { name: /Mirror camera selection/ }));
        await userEvent.selectOptions(screen.getByRole('listbox'), screen.getByRole('option', { name: 'On' }));
        expect(setIsMirrored).toHaveBeenCalledWith(true);
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
