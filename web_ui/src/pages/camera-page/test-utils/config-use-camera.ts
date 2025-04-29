// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { UseQueryResult } from '@tanstack/react-query';

import { Screenshot, UserCameraPermission } from '../../camera-support/camera.interface';
import { useCamera, UseCameraProps } from '../../camera-support/use-camera.hook';
import { UseCameraStorage, useCameraStorage } from '../hooks/use-camera-storage.hook';

jest.mock('../hooks/use-camera-storage.hook', () => ({
    ...jest.requireActual('../hooks/use-camera-storage.hook'),
    useCameraStorage: jest.fn(),
}));
jest.mock('../../camera-support/use-camera.hook', () => ({
    ...jest.requireActual('../../camera-support/use-camera.hook'),
    useCamera: jest.fn(),
}));

export const configUseCamera = ({ ...options }: Partial<UseCameraProps>) => {
    //exception - unstable_flushDiscreteUpdates
    //https://stackoverflow.com/questions/62732346/test-exception-unstable-flushdiscreteupdates
    Object.defineProperty(HTMLMediaElement.prototype, 'muted', {
        set: jest.fn(),
    });

    jest.mocked(useCamera).mockReturnValue({
        screenshots: [],
        availableDevices: [],
        webcamRef: { current: { video: document.createElement('video') } },
        handleImageCapture: jest.fn(),
        handleGetMediaDevices: jest.fn(),
        handleDeleteAllScreenshots: jest.fn(),
        userPermissions: UserCameraPermission.GRANTED,
        handleGetBrowserPermissions: jest.fn(),
        ...options,
    } as unknown as UseCameraProps);
};

export const configUseCameraStorage = ({
    filesData = [],
    ...options
}: Partial<UseCameraStorage> & { filesData?: Screenshot[] }) => {
    jest.mocked(useCameraStorage).mockReturnValue({
        deleteMany: jest.fn().mockResolvedValue(''),
        saveMedia: jest.fn().mockResolvedValue(''),
        updateMany: jest.fn().mockResolvedValue(''),
        deleteAllItems: jest.fn().mockResolvedValue(''),
        invalidateCameraStorageQuery: jest.fn().mockResolvedValue(''),
        savedFilesQuery: {
            data: filesData,
            refetch: jest.fn().mockResolvedValue({ data: filesData }),
        } as unknown as UseQueryResult<Screenshot[]>,
        ...options,
    });
};
