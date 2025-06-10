// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';
import Webcam from 'react-webcam';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { useDeviceSettings } from '../../providers/device-settings-provider.component';
import { VideoRecordingProvider } from '../../providers/video-recording-provider.component';
import { getUseCameraParams } from '../../test-utils/camera-params';
import { getUseCameraSettings } from '../../test-utils/camera-setting';
import { configUseCamera, configUseCameraStorage } from '../../test-utils/config-use-camera';
import { Camera } from './camera.component';

jest.mock('../../providers/device-settings-provider.component', () => ({
    ...jest.requireActual('../../providers/device-settings-provider.component'),
    useDeviceSettings: jest.fn(),
}));

jest.mock('../../../../shared/navigator-utils', () => ({
    ...jest.requireActual('../../../../shared/navigator-utils'),
    getVideoDevices: jest.fn().mockResolvedValue([]),
}));

jest.mock('../../hooks/camera-params.hook', () => ({
    ...jest.requireActual('../../hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

const renderApp = async ({
    webcamRef = { current: { stream: {} } } as React.RefObject<Webcam>,
    isPhotoCaptureMode = true,
    loadDeviceCapabilities = jest.fn(),
}: {
    webcamRef?: React.RefObject<Webcam>;
    loadDeviceCapabilities?: jest.Mock;
    isPhotoCaptureMode?: boolean;
}) => {
    configUseCamera({});
    configUseCameraStorage({});
    jest.mocked(useDeviceSettings).mockReturnValue(getUseCameraSettings({ loadDeviceCapabilities, webcamRef }));
    jest.mocked(useCameraParams).mockReturnValue(getUseCameraParams({ isPhotoCaptureMode }));

    render(
        <VideoRecordingProvider>
            <Camera selectedLabels={[]} />
        </VideoRecordingProvider>,
        {
            featureFlags: { FEATURE_FLAG_CAMERA_VIDEO_UPLOAD: true },
        }
    );
};

describe('Camera', () => {
    const loadStartEvent = new Event('loadstart', { bubbles: true });

    it('capture switch is visible', async () => {
        await renderApp({});

        expect(screen.getByRole('button', { name: /video mode/i })).toBeVisible();
        expect(screen.getByRole('button', { name: /Photo mode/i })).toBeVisible();
    });

    it('render video capture button', async () => {
        await renderApp({ isPhotoCaptureMode: false });

        expect(screen.getByRole('button', { name: /video capture/i })).toBeVisible();
    });

    it('render photo capture button', async () => {
        await renderApp({ isPhotoCaptureMode: true });

        expect(screen.getByRole('button', { name: /photo capture/i })).toBeVisible();
    });

    it('calls onStreamReady', async () => {
        const mockedLoadDeviceCapabilities = jest.fn();
        const mockedStream = {};
        const webcamRef = { current: { stream: {} } } as React.RefObject<Webcam>;

        Object.defineProperty(webcamRef, 'current', {
            set: (info) => info,
            get: () => ({ stream: mockedStream }),
        });

        await renderApp({ loadDeviceCapabilities: mockedLoadDeviceCapabilities, webcamRef });
        fireEvent(screen.getByLabelText('video camera'), loadStartEvent);

        expect(mockedLoadDeviceCapabilities).toHaveBeenCalledWith(mockedStream);
    });

    it('falsy stream, do not call OnStreamReady', async () => {
        const mockedLoadDeviceCapabilities = jest.fn();

        await renderApp({ loadDeviceCapabilities: mockedLoadDeviceCapabilities });
        fireEvent(screen.getByLabelText('video camera'), loadStartEvent);

        expect(mockedLoadDeviceCapabilities).not.toHaveBeenCalled();
    });
});
