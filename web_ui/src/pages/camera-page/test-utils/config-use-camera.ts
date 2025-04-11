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
