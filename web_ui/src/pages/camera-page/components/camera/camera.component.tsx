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

import { Flex, Text, View } from '@adobe/react-spectrum';
import Webcam from 'react-webcam';

import { Label } from '../../../../core/labels/label.interface';
import { formatToHourMinSec } from '../../../../shared/time-utils';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { useDeviceSettings } from '../../providers/device-settings-provider.component';
import { useVideoRecording } from '../../providers/video-recording-provider.component';
import { CaptureModeButton } from '../action-buttons/capture-mode-button.component';
import { CapturePhotoButton } from '../action-buttons/capture-photo-button.component';
import { CaptureVideoButton } from '../action-buttons/capture-video-button.component';

import classes from '../camera-page.module.scss';

interface CameraFactoryProps {
    selectedLabels: Label[];
}
const VideoTiming = () => {
    const { recordedSeconds } = useVideoRecording();

    return <Text UNSAFE_className={classes.recordingCounter}>{formatToHourMinSec(recordedSeconds)}</Text>;
};

export const Camera = ({ selectedLabels }: CameraFactoryProps): JSX.Element => {
    const { isLivePrediction, isPhotoCaptureMode } = useCameraParams();
    const { webcamRef, selectedDeviceId, loadDeviceCapabilities } = useDeviceSettings();

    const CaptureButton = isPhotoCaptureMode ? CapturePhotoButton : CaptureVideoButton;

    return (
        <>
            {!isPhotoCaptureMode && <VideoTiming />}
            <Webcam
                mirrored
                ref={webcamRef}
                aria-label='video camera'
                className={classes.webCam}
                onLoadStart={() => {
                    if (webcamRef.current?.stream) {
                        loadDeviceCapabilities(webcamRef.current?.stream);
                    }
                }}
                videoConstraints={{ deviceId: { exact: selectedDeviceId } }}
            />
            <Flex width={'100%'} marginTop={'size-250'} direction={'row'}>
                <Flex width={'20%'} alignSelf={'center'}>
                    {!isLivePrediction && <CaptureModeButton />}
                </Flex>
                <Flex width={'60%'} justifyContent={'center'}>
                    <CaptureButton webcamRef={webcamRef} selectedLabels={selectedLabels} />
                </Flex>
                <View width={'20%'}></View>
            </Flex>
        </>
    );
};
