// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { MissingProviderError } from '../../../shared/missing-provider-error';
import { getVideoDevices } from '../../../shared/navigator-utils';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { DeviceSettingsProvider, useDeviceSettings } from './device-settings-provider.component';
import { getBrowserPermissions, getValidCapabilities, mergeSettingAndCapabilities } from './util';

jest.mock('../../../shared/navigator-utils', () => ({
    ...jest.requireActual('../../../shared/navigator-utils'),
    getVideoDevices: jest.fn().mockResolvedValue([]),
}));

jest.mock('./util', () => ({
    ...jest.requireActual('./util'),
    getValidCapabilities: jest.fn(),
    mergeSettingAndCapabilities: jest.fn(),
    getBrowserPermissions: jest.fn().mockResolvedValue({
        permissions: {},
        stream: { getTracks: jest.fn(() => []) } as unknown as MediaStream,
    }),
}));

const deviceCapabilities = {
    width: { max: 20, min: 1 },
    height: { max: 20, min: 1 },
    facingMode: [],
    deviceId: '63614d3ea4209ecb8adadad4936b12bd4d8c96642428ac34cde001225abe002a',
};

const deviceSettings = {
    width: 10,
    height: 10,
};

describe('VideoRecordingProvider', () => {
    const renderApp = ({ mockedStream }: { mockedStream?: MediaStream }) => {
        const ProviderOptions = () => {
            const { loadDeviceCapabilities, deviceConfig } = useDeviceSettings();
            return (
                <>
                    <p>{`deviceConfig: ${deviceConfig}`}</p>
                    <button onClick={() => mockedStream && loadDeviceCapabilities(mockedStream)}>
                        loadDeviceCapabilities
                    </button>
                </>
            );
        };

        return render(
            <DeviceSettingsProvider>
                <ProviderOptions />
            </DeviceSettingsProvider>
        );
    };

    describe('provider mounted', () => {
        it('resolves Browser Permissions and video devices', async () => {
            renderApp({});

            await waitFor(() => {
                expect(getVideoDevices).toHaveBeenCalled();
                expect(getBrowserPermissions).toHaveBeenCalled();
            });
        });

        it('filter device', async () => {
            const mockedStream = {
                getVideoTracks: () => [
                    { getCapabilities: () => deviceCapabilities, getSettings: () => deviceSettings },
                ],
            } as unknown as MediaStream;

            renderApp({ mockedStream });

            fireEvent.click(screen.getByRole('button', { name: 'loadDeviceCapabilities' }));

            expect(getValidCapabilities).toHaveBeenCalled();
            expect(mergeSettingAndCapabilities).toHaveBeenCalled();
        });
    });

    it('provider error', async () => {
        const SimpleApp = () => {
            useDeviceSettings();
            return <p>userPermissions</p>;
        };

        try {
            render(<SimpleApp />);
        } catch (error: unknown) {
            expect((error as MissingProviderError).message).toBe(
                'useDeviceSettings must be used within a DeviceSettingsProvider'
            );
        }
    });
});
