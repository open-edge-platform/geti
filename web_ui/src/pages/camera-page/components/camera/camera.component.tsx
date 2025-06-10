// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View } from '@geti/ui';

import { Label } from '../../../../core/labels/label.interface';
import { formatToHourMinSec } from '../../../../shared/time-utils';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { useDeviceSettings } from '../../providers/device-settings-provider.component';
import { useVideoRecording } from '../../providers/video-recording-provider.component';
import { CaptureModeButton } from '../action-buttons/capture-mode-button.component';
import { CapturePhotoButton } from '../action-buttons/capture-photo-button.component';
import { CaptureVideoButton } from '../action-buttons/capture-video-button.component';
import { CameraView } from './camera-view.component';

import classes from '../camera-page.module.scss';

interface CameraFactoryProps {
    selectedLabels: Label[];
}
const VideoTiming = () => {
    const { recordedSeconds } = useVideoRecording();

    return <Text UNSAFE_className={classes.recordingCounter}>{formatToHourMinSec(recordedSeconds)}</Text>;
};

export const Camera = ({ selectedLabels }: CameraFactoryProps): JSX.Element => {
    const { isPhotoCaptureMode } = useCameraParams();
    const { webcamRef } = useDeviceSettings();

    const CaptureButton = isPhotoCaptureMode ? CapturePhotoButton : CaptureVideoButton;

    return (
        <>
            {!isPhotoCaptureMode && <VideoTiming />}
            <CameraView className={classes.webCam} />
            <Flex width={'100%'} marginTop={'size-250'} direction={'row'}>
                <Flex width={'20%'} alignSelf={'center'}>
                    <CaptureModeButton />
                </Flex>
                <Flex width={'60%'} justifyContent={'center'}>
                    <CaptureButton webcamRef={webcamRef} selectedLabels={selectedLabels} />
                </Flex>
                <View width={'20%'}></View>
            </Flex>
        </>
    );
};
