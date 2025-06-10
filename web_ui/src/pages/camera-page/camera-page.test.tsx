// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { MediaUploadProvider } from '../../providers/media-upload-provider/media-upload-provider.component';
import { getEstimateFreeStorage } from '../../shared/navigator-utils';
import { getMockedProjectIdentifier } from '../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { TaskProvider } from '../annotator/providers/task-provider/task-provider.component';
import { UserCameraPermission } from '../camera-support/camera.interface';
import { ProjectProvider } from '../project-details/providers/project-provider/project-provider.component';
import { CameraPage } from './camera-page.component';
import { useCameraParams } from './hooks/camera-params.hook';
import { DeviceSettingsProvider } from './providers/device-settings-provider.component';
import { getUseCameraParams } from './test-utils/camera-params';
import { configUseCamera } from './test-utils/config-use-camera';
import { TOO_LOW_FREE_STORAGE_IN_BYTES, TOO_LOW_FREE_STORAGE_MESSAGE } from './util';

jest.mock('../camera-support/use-camera.hook');

jest.mock('../../shared/navigator-utils', () => ({
    ...jest.requireActual('../../shared/navigator-utils'),
    getVideoDevices: jest.fn().mockResolvedValue([]),
    getEstimateFreeStorage: jest.fn().mockResolvedValue([]),
}));

jest.mock('./hooks/camera-params.hook', () => ({
    ...jest.requireActual('./hooks/camera-params.hook'),
    useCameraParams: jest.fn(),
}));

describe('CameraPage', () => {
    const renderApp = async ({
        cameraPermission,
        mockedGetBrowserPermissions = jest.fn(),
    }: {
        cameraPermission: UserCameraPermission;
        mockedGetBrowserPermissions?: jest.Mock;
    }) => {
        jest.mocked(useCameraParams).mockReturnValue(getUseCameraParams({}));

        configUseCamera({
            userPermissions: cameraPermission,
            handleGetBrowserPermissions: mockedGetBrowserPermissions,
        });

        render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
                <TaskProvider>
                    <DeviceSettingsProvider>
                        <MediaUploadProvider>
                            <CameraPage />
                        </MediaUploadProvider>
                    </DeviceSettingsProvider>
                </TaskProvider>
            </ProjectProvider>
        );
        await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('action buttons are disable', () => {
        it.each([UserCameraPermission.PENDING, UserCameraPermission.DENIED, UserCameraPermission.ERRORED])(
            'cameraPermission: %o',
            async (cameraPermission) => {
                await renderApp({ cameraPermission });

                expect(screen.getByRole('button', { name: /accept/i })).toBeDisabled();
                expect(screen.getByRole('button', { name: /cancel/i })).toBeEnabled();
            }
        );
    });

    it('low storage shows warning message', async () => {
        jest.mocked(getEstimateFreeStorage).mockResolvedValue(TOO_LOW_FREE_STORAGE_IN_BYTES - 1);

        await renderApp({ cameraPermission: UserCameraPermission.GRANTED });

        expect(screen.getByText(TOO_LOW_FREE_STORAGE_MESSAGE)).toBeVisible();
    });

    it('enough storage', async () => {
        jest.mocked(getEstimateFreeStorage).mockResolvedValue(TOO_LOW_FREE_STORAGE_IN_BYTES + 1);

        await renderApp({ cameraPermission: UserCameraPermission.GRANTED });

        expect(screen.queryByText(TOO_LOW_FREE_STORAGE_MESSAGE)).not.toBeInTheDocument();
    });
});
