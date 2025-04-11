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

import { createContext, ReactNode, useContext, useEffect, useRef, useState } from 'react';

import { MissingProviderError } from '../../../shared/missing-provider-error';
import { runWhen } from '../../../shared/utils';
import { useDeviceSettings } from './device-settings-provider.component';

// webm is the only one format with full support on all browsers
//https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#webm
export enum VideoFormat {
    WEBM = 'webm',
}

export enum DataEvents {
    Stop = 'stop',
    DataAvailable = 'dataavailable',
}

export interface RecordingConfigProps {
    name: string;
    format: VideoFormat;
    onVideoReady: (file: File) => void;
}

export interface VideoRecordingContextProps {
    isRecording: boolean;
    recordedSeconds: number;
    recordingConfig: ({ format, name, onVideoReady }: RecordingConfigProps) => {
        startRecording: () => void;
        stopRecording: () => void;
    };
}

const ONE_SECOND = 1000;
const VideoRecordingContext = createContext<VideoRecordingContextProps | undefined>(undefined);

const onValidChunk = runWhen<BlobEvent>(({ data }) => data.size > 0);

export const VideoRecordingProvider = ({ children }: { children: ReactNode }) => {
    const { webcamRef } = useDeviceSettings();
    const timeoutId = useRef<ReturnType<typeof setInterval> | null>(null);
    const recordedChunks = useRef<Blob[]>([]);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);

    const [isRecording, setIsRecording] = useState(false);
    const [recordedSeconds, setRecordedSeconds] = useState(0);

    useEffect(() => {
        return () => {
            timeoutId.current && clearInterval(timeoutId.current);
        };
    }, []);

    const recordingConfig = ({ format, name, onVideoReady }: RecordingConfigProps) => {
        const videoStream = webcamRef.current?.stream;

        const startRecording = (): void => {
            if (mediaRecorderRef.current || !videoStream) {
                return;
            }

            setIsRecording(true);

            timeoutId.current = setInterval(() => setRecordedSeconds((prev) => prev + 1), ONE_SECOND);
            mediaRecorderRef.current = new MediaRecorder(videoStream, { mimeType: `video/webm;codecs=av1` });

            mediaRecorderRef.current.addEventListener(
                DataEvents.DataAvailable,
                onValidChunk(({ data }: BlobEvent) => recordedChunks.current.push(data))
            );

            mediaRecorderRef.current.addEventListener(DataEvents.Stop, () => {
                onVideoReady(new File(recordedChunks.current, `${name}.${format}`, { type: `video/${format}` }));

                recordedChunks.current = [];
            });

            mediaRecorderRef.current.start();
        };

        const stopRecording = () => {
            if (mediaRecorderRef.current) {
                mediaRecorderRef.current.stop();
                setIsRecording(false);
                setRecordedSeconds(0);
            }

            mediaRecorderRef.current = null;
            timeoutId.current && clearInterval(timeoutId.current);
        };

        return { startRecording, stopRecording };
    };

    return (
        <VideoRecordingContext.Provider
            value={{
                recordedSeconds,
                isRecording,
                recordingConfig,
            }}
        >
            {children}
        </VideoRecordingContext.Provider>
    );
};

export const useVideoRecording = (): VideoRecordingContextProps => {
    const context = useContext(VideoRecordingContext);

    if (context === undefined) {
        throw new MissingProviderError('useVideoRecording', 'VideoRecordingProvider');
    }

    return context;
};
