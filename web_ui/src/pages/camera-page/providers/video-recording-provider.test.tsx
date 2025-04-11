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

import { RefObject } from 'react';

import { fireEvent, screen, waitFor } from '@testing-library/react';
import Webcam from 'react-webcam';

import { MissingProviderError } from '../../../shared/missing-provider-error';
import { delay } from '../../../shared/utils';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { getUseCameraSettings } from '../test-utils/camera-setting';
import { useDeviceSettings } from './device-settings-provider.component';
import {
    RecordingConfigProps,
    useVideoRecording,
    VideoFormat,
    VideoRecordingProvider,
} from './video-recording-provider.component';

jest.mock('./device-settings-provider.component', () => ({
    useDeviceSettings: jest.fn(),
}));

const mockMediaRecorder = (chunk: Blob) => {
    const mockedMediaRecorder = jest.fn(() => ({
        start: jest.fn(),
        stop: jest.fn(),
        pause: jest.fn(),
        resume: jest.fn(),
        addEventListener: jest.fn((_type, callback) => callback({ data: chunk })),
    }));

    Object.defineProperty(global, 'MediaRecorder', {
        writable: true,
        value: mockedMediaRecorder.mockName('MediaRecorder'),
    });

    return mockedMediaRecorder;
};
describe('VideoRecordingProvider', () => {
    const renderApp = async (recordingConfigProps: RecordingConfigProps & { mediaStream: MediaStream | null }) => {
        jest.mocked(useDeviceSettings).mockReturnValue(
            getUseCameraSettings({
                webcamRef: { current: { stream: recordingConfigProps.mediaStream } } as RefObject<Webcam>,
            })
        );

        const ProviderOptions = () => {
            const { isRecording, recordedSeconds, recordingConfig } = useVideoRecording();
            const { startRecording, stopRecording } = recordingConfig(recordingConfigProps);

            return (
                <>
                    <p>isRecording: {String(isRecording)}</p>
                    <p>recordedSeconds: {recordedSeconds}</p>
                    <button onClick={() => stopRecording()}>stopRecording</button>
                    <button onClick={() => startRecording()}>startRecording</button>
                </>
            );
        };
        return render(
            <VideoRecordingProvider>
                <ProviderOptions />
            </VideoRecordingProvider>
        );
    };
    const stopRecordingButton = () => screen.getByRole('button', { name: 'stopRecording' });
    const startRecordingButton = () => screen.getByRole('button', { name: 'startRecording' });

    it('records one second', async () => {
        const mockedMediaStream = {} as unknown as MediaStream;
        const mockedOnVideoReady = jest.fn();
        const mockedMediaRecorder = mockMediaRecorder(new Blob(['file test']));
        const fileName = 'test-name';
        const fileFormat = VideoFormat.WEBM;

        renderApp({
            name: fileName,
            format: fileFormat,
            mediaStream: mockedMediaStream,
            onVideoReady: mockedOnVideoReady,
        });

        fireEvent.click(startRecordingButton());

        await delay(1000);
        expect(screen.getByText('recordedSeconds: 1')).toBeVisible();

        fireEvent.click(stopRecordingButton());

        expect(screen.getByText('recordedSeconds: 0')).toBeVisible();

        expect(mockedMediaRecorder).toHaveBeenCalledWith(mockedMediaStream, {
            mimeType: expect.stringContaining(`video/${fileFormat}`),
        });

        expect(mockedOnVideoReady).toHaveBeenCalledWith(expect.any(File));

        const [file] = mockedOnVideoReady.mock.calls.at(-1);
        expect(file.name).toContain(`${fileName}.${fileFormat}`);
        expect(file.type).toContain(`video/${fileFormat}`);
    });

    it('MediaStream is falsy, does not record', async () => {
        const mockedMediaRecorder = mockMediaRecorder(new Blob(['file test']));

        renderApp({
            name: 'test-name',
            format: VideoFormat.WEBM,
            mediaStream: null,
            onVideoReady: jest.fn(),
        });

        fireEvent.click(startRecordingButton());

        await waitFor(() => {
            expect(screen.getByText('isRecording: false')).toBeVisible();
            expect(mockedMediaRecorder).not.toHaveBeenCalled();
        });
    });

    it('provider error', async () => {
        const SimpleApp = () => {
            const { isRecording } = useVideoRecording();
            return <p>isRecording: {String(isRecording)}</p>;
        };

        try {
            render(<SimpleApp />);
        } catch (error: unknown) {
            expect((error as MissingProviderError).message).toBe(
                'useVideoRecording must be used within a VideoRecordingProvider'
            );
        }
    });
});
