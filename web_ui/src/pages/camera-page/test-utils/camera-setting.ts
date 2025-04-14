// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import Webcam from 'react-webcam';

import { UserCameraPermission } from '../../camera-support/camera.interface';
import { SettingsContextProps } from '../providers/device-settings-provider.component';

export const getUseCameraSettings = ({ stream, ...options }: Partial<SettingsContextProps & { stream: unknown }>) => ({
    webcamRef: { current: { stream } } as React.RefObject<Webcam>,
    videoDevices: [],
    deviceConfig: [],
    selectedDeviceId: '',
    userPermissions: UserCameraPermission.PENDING,
    applySettings: jest.fn(),
    loadDeviceCapabilities: jest.fn(),
    setSelectedDeviceId: jest.fn(),
    ...options,
});
