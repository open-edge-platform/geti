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

import {
    createContext,
    Dispatch,
    ReactNode,
    RefObject,
    SetStateAction,
    useContext,
    useEffect,
    useRef,
    useState,
} from 'react';

import Webcam from 'react-webcam';
import { useIsMounted } from 'usehooks-ts';

import { MissingProviderError } from '../../../shared/missing-provider-error';
import { getVideoDevices } from '../../../shared/navigator-utils';
import { runWhen } from '../../../shared/utils';
import { UserCameraPermission } from '../../camera-support/camera.interface';
import { DeviceConfiguration, getBrowserPermissions, getValidCapabilities, mergeSettingAndCapabilities } from './util';

export interface SettingsContextProps {
    webcamRef: RefObject<Webcam>;
    videoDevices: MediaDeviceInfo[];
    selectedDeviceId: string | undefined;
    deviceConfig: DeviceConfiguration[];
    userPermissions: UserCameraPermission;
    loadDeviceCapabilities: (stream: MediaStream) => void;
    setSelectedDeviceId: Dispatch<SetStateAction<string | undefined>>;
}

const SettingsContext = createContext<SettingsContextProps | undefined>(undefined);

export const DeviceSettingsProvider = ({ children }: { children: ReactNode }) => {
    const isMounted = useIsMounted();
    const webcamRef = useRef<Webcam>(null);
    const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([]);
    const [deviceConfig, setDeviceConfig] = useState<DeviceConfiguration[]>([]);
    const [userPermissions, setUserPermissions] = useState(UserCameraPermission.PENDING);
    const [selectedDeviceId, setSelectedDeviceId] = useState<string | undefined>(undefined);

    const onComponentIsMounted = runWhen<MediaDeviceInfo[]>(isMounted);

    useEffect(() => {
        getBrowserPermissions().then(({ permissions, stream }) => {
            // Stop the stream because react-webcam starts its own stream
            stream && stream.getTracks().forEach((track) => track.stop());

            getVideoDevices().then(
                onComponentIsMounted((newDevices: MediaDeviceInfo[]) => {
                    setVideoDevices(newDevices);
                    setUserPermissions(permissions);
                    setSelectedDeviceId(newDevices.at(0)?.deviceId ?? '');
                })
            );
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const loadDeviceCapabilities = (stream: MediaStream) => {
        const [videoTrack] = stream.getVideoTracks();
        const filteredValidCapabilities = getValidCapabilities(videoTrack.getCapabilities());
        const newDevicesConfig = mergeSettingAndCapabilities(filteredValidCapabilities, videoTrack.getSettings());

        setDeviceConfig(newDevicesConfig);
    };

    return (
        <SettingsContext.Provider
            value={{
                webcamRef,
                videoDevices,
                deviceConfig,
                userPermissions,
                selectedDeviceId,
                setSelectedDeviceId,
                loadDeviceCapabilities,
            }}
        >
            {children}
        </SettingsContext.Provider>
    );
};

export const useDeviceSettings = (): SettingsContextProps => {
    const context = useContext(SettingsContext);

    if (context === undefined) {
        throw new MissingProviderError('useDeviceSettings', 'DeviceSettingsProvider');
    }

    return context;
};
