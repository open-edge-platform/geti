// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { RefObject, useCallback, useRef, useState } from 'react';

import isEmpty from 'lodash/isEmpty';
import Webcam from 'react-webcam';
import { v4 as uuid } from 'uuid';

import { getVideoDevices } from '../../shared/navigator-utils';
import { downloadFile, hasEqualId } from '../../shared/utils';
import { FacingMode, Screenshot, UserCameraPermission, UserCameraPermissionError } from './camera.interface';

export interface UseCameraProps {
    webcamRef: RefObject<Webcam>;

    handleDownloadImage: (screenshotId: string) => void;
    handleDownloadVideo: () => void;
    handleStartVideoCapture: () => void;
    handleStopVideoCapture: () => void;
    handleImageCapture: () => void;

    handleGetMediaDevices: () => void;
    switchActiveDevice: () => void;
    handleGetBrowserPermissions: () => Promise<void>;

    mediaConstraints: Partial<MediaTrackSettings>;
    availableDevices: MediaDeviceInfo[];
    screenshots: Omit<Screenshot, 'file' | 'labelIds'>[];
    recordingVideo: boolean;
    userPermissions: UserCameraPermission;
}

const defaultMediaConstraints: Partial<MediaTrackSettings> = {
    facingMode: FacingMode.USER,
};

export const useCamera = (): UseCameraProps => {
    const webcamRef = useRef<Webcam>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);

    const [recordingVideo, setRecordingVideo] = useState(false);
    const [recordedChunks, setRecordedChunks] = useState<Blob[]>([]);
    const [mediaConstraints, setMediaConstraints] = useState(defaultMediaConstraints);
    const [availableDevices, setAvailableDevices] = useState<MediaDeviceInfo[]>([]);
    const [screenshots, setScreenshots] = useState<Omit<Screenshot, 'file' | 'labelIds'>[]>([]);
    const [userPermissions, setUserPermissions] = useState(UserCameraPermission.PENDING);

    const handleGetBrowserPermissions = async (): Promise<void> => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });

            setUserPermissions(UserCameraPermission.GRANTED);

            // Stop the stream because react-webcam starts its own stream
            stream.getTracks().forEach((track) => track.stop());
        } catch (error: unknown) {
            const errorType = error instanceof Error ? error.message : '';

            if (errorType === UserCameraPermissionError.NOT_ALLOWED) {
                setUserPermissions(UserCameraPermission.DENIED);
            } else {
                setUserPermissions(UserCameraPermission.ERRORED);
            }
        }
    };

    const handleImageCapture = useCallback(async () => {
        if (webcamRef.current) {
            const dataUrl = webcamRef.current.getScreenshot();

            if (dataUrl) {
                setScreenshots((prev) => [...prev, { id: uuid(), dataUrl, labelName: null }]);
            }
        }
    }, [webcamRef]);

    const handleDataAvailable = useCallback(
        ({ data }: { data: Blob }): void => {
            if (data.size > 0) {
                setRecordedChunks((prev) => prev.concat(data));
            }
        },
        [setRecordedChunks]
    );

    const handleStartVideoCapture = useCallback((): void => {
        setRecordingVideo(true);

        if (!mediaRecorderRef.current && webcamRef.current?.stream) {
            // TODO: Update this mimeType if necessary.
            // https://developer.mozilla.org/en-US/docs/Web/Media/Formats/codecs_parameter
            mediaRecorderRef.current = new MediaRecorder(webcamRef.current.stream, {
                mimeType: 'video/webm',
            });
            mediaRecorderRef.current.addEventListener('dataavailable', handleDataAvailable);
            mediaRecorderRef.current.start();
        }
    }, [handleDataAvailable]);

    const handleStopVideoCapture = useCallback((): void => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
        }

        setRecordingVideo(false);
    }, [mediaRecorderRef, setRecordingVideo]);

    const handleDownloadImage = useCallback(
        (id: string): void => {
            if (isEmpty(screenshots)) {
                console.info('No screenshots taken, could not download image.');

                return;
            }

            const screenshot = screenshots.find(hasEqualId(id));

            if (screenshot?.dataUrl) {
                // We need to convert the dataUrl into a blob
                // Why?: https://bugs.chromium.org/p/chromium/issues/detail?id=742702
                fetch(screenshot.dataUrl)
                    .then((res) => res.blob())
                    .then((blob) => {
                        downloadFile(window.URL.createObjectURL(blob), `capture-${id}`);
                    });
            }
        },
        [screenshots]
    );

    const handleDownloadVideo = useCallback((): void => {
        if (isEmpty(recordedChunks)) {
            console.info('No blob chunks recorded, could not download video.');

            return;
        }

        const blob = new Blob(recordedChunks, {
            // TODO: Update this mimeType if necessary.
            // https://developer.mozilla.org/en-US/docs/Web/Media/Formats/codecs_parameter
            type: 'video/webm',
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');

        document.body.appendChild(a);

        downloadFile(URL.createObjectURL(blob), 'geti-recording.webm');

        window.URL.revokeObjectURL(url);

        setRecordedChunks([]);
    }, [recordedChunks]);

    const handleGetMediaDevices = async (): Promise<void> => {
        try {
            const devices: MediaDeviceInfo[] = await getVideoDevices();

            setAvailableDevices(devices);
        } catch (error: unknown) {
            console.error(error);
        }
    };

    const switchActiveDevice = (): void => {
        setMediaConstraints((constraints) => ({
            ...constraints,
            facingMode: mediaConstraints.facingMode === 'user' ? FacingMode.ENVIRONMENT : FacingMode.USER,
        }));
    };

    return {
        webcamRef,
        handleDownloadVideo,
        handleDownloadImage,
        handleStartVideoCapture,
        handleStopVideoCapture,
        handleImageCapture,
        handleGetBrowserPermissions,
        handleGetMediaDevices,
        switchActiveDevice,
        mediaConstraints,
        availableDevices,
        screenshots,
        userPermissions,
        recordingVideo,
    };
};
