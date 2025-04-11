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
