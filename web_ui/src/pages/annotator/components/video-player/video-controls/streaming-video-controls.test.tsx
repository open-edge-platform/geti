// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, renderHook, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';
import partial from 'lodash/partial';

import { createInMemoryInferenceService } from '../../../../../core/annotations/services/in-memory-inference-service';
import { createInMemoryModelsService } from '../../../../../core/models/services/in-memory-models-service';
import { ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { ApplicationServicesContextProps } from '../../../../../core/services/application-services-provider.component';
import { ANNOTATOR_MODE } from '../../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import { annotatorRender as render } from '../../../test-utils/annotator-render';
import {
    useStreamingVideoPlayer,
    VideoPlayerPlayerContextProps,
} from '../streaming-video-player/streaming-video-player-provider.component';
import { BufferStatus } from '../streaming-video-player/utils';
import {
    StreamingVideoControls,
    usePauseResumeVideoBuffering,
    usePauseResumeVideoBufferingProps,
} from './streaming-video-controls.component';
import { getMockedVideoControls } from './test-utils';
import { VideoControls } from './video-controls.interface';

jest.mock('../streaming-video-player/streaming-video-player-provider.component', () => ({
    ...jest.requireActual('../streaming-video-player/streaming-video-player-provider.component'),
    useStreamingVideoPlayer: jest.fn(),
}));

jest.mock('../../../hooks/use-annotator-mode', () => ({
    ...jest.requireActual('../../../hooks/use-annotator-mode'),
    useAnnotatorMode: jest.fn(),
}));

const setupStreamVideoPlayer = (props: Partial<VideoPlayerPlayerContextProps>) => {
    const config = {
        isMuted: false,
        setIsMuted: jest.fn(),
        videoPlayerError: undefined,
        buffers: [],
        isBuffering: false,
        currentIndex: 0,
        isPlaying: false,
    } as unknown as VideoPlayerPlayerContextProps;
    jest.mocked(useStreamingVideoPlayer).mockReturnValue({ ...config, ...props });
};

const mockedBuffer = (index: number) => ({
    startFrame: index,
    endFrame: index + 1,
    frameSkip: 0,
    status: BufferStatus.SUCCESS,
    mode: 'predictions',
    selectedTaskId: '64a3f63ba9cf45a149c42c17',
});

describe('StreamingVideoControls', () => {
    const renderApp = async (
        videoControls: VideoControls,
        configVideoPlayer: Partial<VideoPlayerPlayerContextProps> = {},
        mode = ANNOTATOR_MODE.ACTIVE_LEARNING,
        services?: Partial<ApplicationServicesContextProps> | undefined
    ) => {
        jest.mocked(useAnnotatorMode).mockReturnValue({
            currentMode: mode,
            isActiveLearningMode: mode === ANNOTATOR_MODE.ACTIVE_LEARNING,
        });
        setupStreamVideoPlayer(configVideoPlayer);

        const result = render(<StreamingVideoControls videoControls={videoControls} />, { services });

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        return result;
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('empty models', () => {
        const modelsService = createInMemoryModelsService();
        modelsService.getModels = jest.fn(async () => []);

        it('allows the user to navigate the video', async () => {
            const videoControls = getMockedVideoControls({});

            await renderApp(videoControls, {}, ANNOTATOR_MODE.ACTIVE_LEARNING, { modelsService });

            fireEvent.click(screen.getByRole('button', { name: 'Go to previous frame' }));
            expect(videoControls.previous).toHaveBeenCalled();

            fireEvent.click(screen.getByRole('button', { name: 'Go to next frame' }));
            expect(videoControls.next).toHaveBeenCalled();

            fireEvent.click(screen.getByRole('button', { name: 'Play video' }));
            expect(videoControls.play).toHaveBeenCalled();
        });

        it('allows the user to play the video', async () => {
            const videoControls = getMockedVideoControls({});
            await renderApp(videoControls, {}, ANNOTATOR_MODE.ACTIVE_LEARNING, { modelsService });

            fireEvent.click(screen.getByRole('button', { name: 'Play video' }));
            expect(videoControls.play).toHaveBeenCalled();
        });
    });

    describe('mute the video', () => {
        const videoControls = getMockedVideoControls({});
        const setIsMuted = jest.fn();

        it('allows the user to mute the video', async () => {
            await renderApp(videoControls, { setIsMuted });

            fireEvent.click(screen.getByRole('button', { name: 'Mute video' }));
            expect(setIsMuted).toHaveBeenCalledWith(true);
        });

        it('allows the user to unmute the video', async () => {
            await renderApp(videoControls, { isMuted: true, setIsMuted });

            fireEvent.click(screen.getByRole('button', { name: 'Unmute video' }));
            expect(setIsMuted).toHaveBeenCalledWith(false);
        });
    });

    describe('play icon', () => {
        const currentIndex = 0;
        const videoControls = getMockedVideoControls({});

        describe('pause video', () => {
            const notBufferedIndex = mockedBuffer(currentIndex + 1);
            const preConfigApp = partial(renderApp, videoControls, {
                isPlaying: true,
                currentIndex,
                isBuffering: false,
                buffers: [notBufferedIndex],
            });

            it('active learning', async () => {
                await preConfigApp(ANNOTATOR_MODE.ACTIVE_LEARNING);
                expect(videoControls.pause).toBeCalledTimes(0);
            });

            it('prediction', async () => {
                await preConfigApp(ANNOTATOR_MODE.PREDICTION);

                await waitFor(() => {
                    expect(videoControls.pause).toBeCalledTimes(1);
                });
            });
        });

        describe('has models', () => {
            describe('it is buffereing', () => {
                const preConfigApp = partial(renderApp, videoControls, { isBuffering: true });

                it('active learning', async () => {
                    await preConfigApp(ANNOTATOR_MODE.ACTIVE_LEARNING);
                    expect(screen.getByRole('button', { name: 'Play video' })).toBeDisabled();
                });

                it('prediction', async () => {
                    await preConfigApp(ANNOTATOR_MODE.PREDICTION);
                    expect(screen.getByRole('button', { name: 'Play video' })).toBeDisabled();
                });
            });

            describe('empty buffer', () => {
                const preConfigApp = partial(renderApp, videoControls, {
                    currentIndex,
                    isBuffering: false,
                    buffers: [],
                });

                it('active learning', async () => {
                    await preConfigApp(ANNOTATOR_MODE.ACTIVE_LEARNING);
                    expect(screen.getByRole('button', { name: 'Play video' })).toBeEnabled();
                });

                it('prediction', async () => {
                    await preConfigApp(ANNOTATOR_MODE.PREDICTION);
                    await waitFor(() => {
                        expect(screen.getByRole('button', { name: 'Play video' })).toBeDisabled();
                    });
                });
            });

            describe('the frame is not buffered yet', () => {
                const notBufferedIndex = mockedBuffer(currentIndex + 1);

                const preConfigApp = partial(renderApp, videoControls, {
                    currentIndex,
                    isBuffering: false,
                    buffers: [notBufferedIndex],
                });

                it('active learning', async () => {
                    await preConfigApp(ANNOTATOR_MODE.ACTIVE_LEARNING);
                    expect(screen.getByRole('button', { name: 'Play video' })).toBeEnabled();
                });

                it('prediction', async () => {
                    await preConfigApp(ANNOTATOR_MODE.PREDICTION);
                    await waitFor(() => {
                        expect(screen.getByRole('button', { name: 'Play video' })).toBeDisabled();
                    });
                });
            });

            describe('inference server is not ready', () => {
                const bufferedIndex = mockedBuffer(currentIndex - 1);
                const inferenceService = createInMemoryInferenceService();
                inferenceService.getInferenceServerStatus = async (_projectIdentifier: ProjectIdentifier) => ({
                    isInferenceServerReady: false,
                });

                const preConfigApp = partial(renderApp, videoControls, {
                    currentIndex,
                    isBuffering: false,
                    buffers: [bufferedIndex],
                });

                it('active learning', async () => {
                    await preConfigApp(ANNOTATOR_MODE.ACTIVE_LEARNING, { inferenceService });
                    expect(screen.getByRole('button', { name: 'Play video' })).toBeEnabled();
                });

                it('prediction', async () => {
                    await preConfigApp(ANNOTATOR_MODE.PREDICTION, { inferenceService });

                    await waitFor(() => {
                        expect(screen.getByRole('button', { name: 'Play video' })).toBeDisabled();
                    });
                });
            });
        });
    });

    describe('usePauseResumeVideoBuffering', () => {
        const videoControls = getMockedVideoControls({});
        it('pause video', () => {
            renderHook((config: usePauseResumeVideoBufferingProps) => usePauseResumeVideoBuffering(config), {
                initialProps: { isPlaying: true, isBufferedFrame: false, hasEmptyBuffers: false, videoControls },
            });

            expect(videoControls.pause).toBeCalledTimes(1);
        });

        it('resume video', () => {
            const { rerender } = renderHook(
                (config: usePauseResumeVideoBufferingProps) => usePauseResumeVideoBuffering(config),
                {
                    initialProps: { isPlaying: true, isBufferedFrame: false, hasEmptyBuffers: false, videoControls },
                }
            );

            expect(videoControls.pause).toBeCalledTimes(1);
            expect(videoControls.play).not.toBeCalled();

            rerender({ isPlaying: false, isBufferedFrame: true, hasEmptyBuffers: false, videoControls });

            expect(videoControls.pause).toBeCalledTimes(1);
            expect(videoControls.play).toBeCalledTimes(1);
        });
    });
});
