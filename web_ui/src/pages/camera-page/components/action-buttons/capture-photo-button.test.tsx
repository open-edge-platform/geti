// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { Task } from '../../../../core/projects/task.interface';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { DeviceSettingsProvider } from '../../providers/device-settings-provider.component';
import { getUseCameraParams } from '../../test-utils/camera-params';
import { configUseCamera, configUseCameraStorage } from '../../test-utils/config-use-camera';
import { CapturePhotoButton } from './capture-photo-button.component';

// This component has animation-transitions that influence the 'onPress' handler,
// that case have been tested on its tests file and hence isn't worth re-doing it here
jest.mock('./capture-button-animation.component', () => ({
    CaptureButtonAnimation: (props: { onPress: () => void }) => <button onClick={props.onPress}>capture photo</button>,
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
    mockedSaveMedia = jest.fn(),
    mockedDeleteAllItems = jest.fn(),
    isLivePrediction = false,
}: {
    tasks?: Task[];
    isLivePrediction?: boolean;

    mockedSaveMedia?: jest.Mock;
    mockedDeleteAllItems?: jest.Mock;
}) => {
    configUseCamera({});

    jest.mocked(useCameraParams).mockReturnValue(getUseCameraParams({ isLivePrediction }));

    configUseCameraStorage({ saveMedia: mockedSaveMedia, deleteAllItems: mockedDeleteAllItems });

    const CameraApp = () => {
        const ref = useRef(null);

        return <CapturePhotoButton webcamRef={ref} selectedLabels={[]} />;
    };

    render(
        <DeviceSettingsProvider>
            <CameraApp />
        </DeviceSettingsProvider>
    );
};

describe('CapturePhotoButton', () => {
    it('live prediction is off, calls SaveMedia', async () => {
        const mockedSaveMedia = jest.fn(() => Promise.resolve());
        const mockedDeleteAllItems = jest.fn(() => Promise.resolve());
        await renderApp({ mockedSaveMedia, mockedDeleteAllItems });

        fireEvent.click(screen.getByRole('button', { name: /capture photo/i }));

        await waitFor(() => {
            expect(mockedSaveMedia).toHaveBeenCalledWith({
                id: expect.any(String),
                labelName: null,
                dataUrl: undefined,
                labelIds: [],
            });
        });

        expect(mockedDeleteAllItems).not.toHaveBeenCalled();
    });

    it('live prediction is on, calls DeleteAllItems', async () => {
        const mockedSaveMedia = jest.fn(() => Promise.resolve());
        const mockedDeleteAllItems = jest.fn(() => Promise.resolve());
        await renderApp({ mockedSaveMedia, mockedDeleteAllItems, isLivePrediction: true });

        fireEvent.click(screen.getByRole('button', { name: /capture photo/i }));

        await waitFor(() => {
            expect(mockedDeleteAllItems).toHaveBeenCalled();
            expect(mockedSaveMedia).toHaveBeenCalled();
        });
    });
});
