// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import Webcam from 'react-webcam';

import { useDeviceSettings } from '../../providers/device-settings-provider.component';

interface CameraViewProps {
    className?: string;
}

export const CameraView = ({ className }: CameraViewProps) => {
    const { webcamRef, selectedDeviceId, loadDeviceCapabilities, isMirrored } = useDeviceSettings();

    return (
        <Webcam
            mirrored={isMirrored}
            ref={webcamRef}
            aria-label='video camera'
            className={className}
            onLoadStart={() => {
                if (webcamRef.current?.stream) {
                    loadDeviceCapabilities(webcamRef.current?.stream);
                }
            }}
            videoConstraints={{ deviceId: { exact: selectedDeviceId } }}
        />
    );
};
