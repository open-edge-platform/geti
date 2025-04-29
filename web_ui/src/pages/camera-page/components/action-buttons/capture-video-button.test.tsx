// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { Label } from '../../../../core/labels/label.interface';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { mockFile } from '../../../../test-utils/mockFile';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { RecordingConfigProps, useVideoRecording } from '../../providers/video-recording-provider.component';
import { configUseCamera, configUseCameraStorage } from '../../test-utils/config-use-camera';
import { CaptureVideoButton } from './capture-video-button.component';

jest.mock('../../providers/video-recording-provider.component', () => ({
    ...jest.requireActual('../../providers/video-recording-provider.component'),
    useVideoRecording: jest.fn(),
}));

jest.mock('../../media-validation-utils', () => ({
    ...jest.requireActual('../../media-validation-utils'),
    validateVideoDimensions: (callback: (file: File) => void) => (video: File) => callback(video),
}));

const renderApp = async ({
    isRecording = false,
    selectedLabels = [],
    callVideoReady = false,
    mockedSaveMedia = jest.fn(),
    mockedStopRecording = jest.fn(),
    mockedStartRecording = jest.fn(),
}: {
    isRecording?: boolean;
    callVideoReady?: boolean;
    selectedLabels?: Label[];
    mockedSaveMedia?: jest.Mock;
    mockedStopRecording?: jest.Mock;
    mockedStartRecording?: jest.Mock;
}) => {
    configUseCamera({});
    configUseCameraStorage({ saveMedia: mockedSaveMedia });

    jest.mocked(useVideoRecording).mockImplementation(() => {
        return {
            isRecording,
            recordedSeconds: 0,
            setVideoStream: jest.fn(),
            recordingConfig: ({ onVideoReady }: RecordingConfigProps) => {
                callVideoReady && onVideoReady(mockFile({}));

                return {
                    stopRecording: mockedStopRecording,
                    startRecording: mockedStartRecording,
                };
            },
        };
    });

    render(<CaptureVideoButton selectedLabels={selectedLabels} />);
};

describe('CaptureVideoButton', () => {
    const mockedSaveMedia = jest.fn().mockResolvedValue('');
    const mockedStopRecording = jest.fn();
    const mockedStartRecording = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('starts video recording', async () => {
        await renderApp({ isRecording: false, mockedStartRecording, mockedStopRecording });

        fireEvent.click(screen.getByRole('button', { name: /video capture/i }));

        await waitFor(() => {
            expect(mockedStopRecording).not.toHaveBeenCalled();
            expect(mockedStartRecording).toHaveBeenCalled();
        });
    });

    it('stops video recording', async () => {
        await renderApp({ isRecording: true, mockedStartRecording, mockedStopRecording });

        fireEvent.click(screen.getByRole('button', { name: /video capture/i }));

        await waitFor(() => {
            expect(mockedStopRecording).toHaveBeenCalled();
            expect(mockedStartRecording).not.toHaveBeenCalled();
        });
    });

    describe('store video', () => {
        it('with selected labels', async () => {
            const mockedLabel = getMockedLabel({ name: 'label-one' });
            await renderApp({
                mockedSaveMedia,
                callVideoReady: true,
                selectedLabels: [mockedLabel],
            });

            await waitFor(() => {
                expect(mockedSaveMedia).toHaveBeenCalledWith({
                    id: expect.any(String),
                    file: expect.anything(),
                    labelIds: [mockedLabel.id],
                    labelName: mockedLabel.name,
                });
            });
        });

        it('without selected labels', async () => {
            await renderApp({
                mockedSaveMedia,
                callVideoReady: true,
                selectedLabels: [],
            });

            await waitFor(() => {
                expect(mockedSaveMedia).toHaveBeenCalledWith({
                    id: expect.any(String),
                    file: expect.anything(),
                    labelIds: [],
                    labelName: null,
                });
            });
        });
    });
});
