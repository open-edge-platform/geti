// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { act, fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryAnnotationService } from '../../../../core/annotations/services/in-memory-annotation-service';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { createInMemoryMediaService } from '../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { isVideoFrame, VideoFrame } from '../../../../core/media/video.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { API_URLS } from '../../../../core/services/urls';
import { LoadingIndicator } from '../../../../shared/components/loading/loading-indicator.component';
import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedVideoFrameMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { useDataset } from '../../providers/dataset-provider/dataset-provider.component';
import { useIsInActiveMode } from '../../providers/dataset-provider/use-is-in-active-mode.hook';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { annotatorRender as render } from '../../test-utils/annotator-render';
import { VideoPlayerProvider } from './video-player-provider.component';
import { VideoPlayer } from './video-player.component';

const mockedDatasetIdentifier = getMockedDatasetIdentifier({
    workspaceId: 'test-workspace',
    projectId: 'test-project',
    datasetId: 'test-dataset',
});

jest.mock('../../hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: jest.fn(() => mockedDatasetIdentifier),
}));

jest.mock('../../providers/dataset-provider/use-is-in-active-mode.hook', () => ({
    useIsInActiveMode: jest.fn(),
}));

const renderVideoPlayer = async (videoFrame: VideoFrame) => {
    const annotationService = createInMemoryAnnotationService();
    const mediaService = createInMemoryMediaService();

    const selectVideoFrame = jest.fn();

    const App = () => {
        const { selectedMediaItem, setSelectedMediaItem } = useSelectedMediaItem();

        useEffect(() => {
            if (selectedMediaItem === undefined || !isVideoFrame(selectedMediaItem)) {
                setSelectedMediaItem(videoFrame);
            }
        }, [selectedMediaItem, setSelectedMediaItem]);

        if (selectedMediaItem !== undefined && isVideoFrame(selectedMediaItem)) {
            return (
                <VideoPlayerProvider videoFrame={videoFrame} selectVideoFrame={selectVideoFrame}>
                    <VideoPlayer />
                </VideoPlayerProvider>
            );
        }

        return <LoadingIndicator />;
    };

    await render(<App />, {
        datasetIdentifier: mockedDatasetIdentifier,
        services: { annotationService, mediaService },
    });

    // Loading indicator for project
    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return { annotationService, selectVideoFrame };
};

describe('Video player', () => {
    beforeEach(() => {
        jest.useFakeTimers();
        jest.mocked(useIsInActiveMode).mockReturnValue(false);
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    const videoFrame = getMockedVideoFrameMediaItem({});

    it('Shows video player controls', async () => {
        await renderVideoPlayer(videoFrame);
        expect(await screen.findByText('Frames')).toBeInTheDocument();
    });

    const getVideoFrame = (frameNumber: number) => {
        const identifier = { ...videoFrame.identifier, frameNumber };
        const src = API_URLS.MEDIA_ITEM_SRC(mockedDatasetIdentifier, identifier);
        const thumbnailSrc = API_URLS.MEDIA_ITEM_THUMBNAIL(mockedDatasetIdentifier, identifier);

        return { ...videoFrame, identifier, src, thumbnailSrc };
    };

    describe('video annotator', () => {
        it('Allows opening the video annotator', async () => {
            await renderVideoPlayer(videoFrame);

            fireEvent.click(await screen.findByRole('button', { name: 'Close video annotator' }));

            fireEvent.click(screen.getByRole('button', { name: 'Open video annotator' }));
        });
    });

    describe('video player', () => {
        const duration = 33 * 3600 + 51 * 60 + 7;
        const frames = duration * 60;
        const fps = frames / duration;
        const metadata = { width: 200, height: 300, fps, frames, duration, frameStride: 60, size: 12345 };

        it('formats the time of a video frame', async () => {
            const mediaItem = getMockedVideoFrameMediaItem({
                metadata,
                identifier: {
                    type: MEDIA_TYPE.VIDEO_FRAME,
                    videoId: 'test-video',
                    frameNumber: fps + fps * 13 * 60 + fps * 3 * 3600,
                },
            });

            await renderVideoPlayer(mediaItem);

            expect(await screen.findByText('03:13:01 / 33:51:07')).toBeInTheDocument();
        });

        it('floors time when formatting the time of a video frame', async () => {
            const mediaItem = getMockedVideoFrameMediaItem({
                metadata,
                identifier: {
                    type: MEDIA_TYPE.VIDEO_FRAME,
                    videoId: 'test-video',
                    frameNumber: 59.95 * fps,
                },
            });

            await renderVideoPlayer(mediaItem);

            expect(await screen.findByText('00:00:59 / 33:51:07')).toBeInTheDocument();
        });

        it('Goes to next frame when playing the video', async () => {
            const { annotationService } = await renderVideoPlayer(videoFrame);
            const spy = jest.spyOn(annotationService, 'getAnnotations');

            fireEvent.click(await screen.findByRole('button', { name: 'Play video' }));

            // By default we play 1 frame per second
            act(() => {
                jest.advanceTimersByTime(1000);
            });

            const pauseButton = screen.getByRole('button', { name: 'Pause video' });
            await waitFor(() => {
                expect(annotationService.getAnnotations).toHaveBeenCalledWith(
                    mockedDatasetIdentifier,
                    expect.anything(),
                    getVideoFrame(videoFrame.identifier.frameNumber + videoFrame.metadata.frameStride)
                );
            });

            fireEvent.click(pauseButton);
            expect(await screen.findByRole('button', { name: 'Play video' })).toBeInTheDocument();
            spy.mockRestore();
        });

        it("Skips video frames while it's still loading a previous frame", async () => {
            const { annotationService } = await renderVideoPlayer(videoFrame);
            let mockTimeout: NodeJS.Timeout | null = null;

            const spy = jest
                .spyOn(annotationService, 'getAnnotations')
                .mockImplementation(async (_dataset, _projectLabels, mediaItem) => {
                    if (isVideoFrame(mediaItem) && mediaItem.identifier.frameNumber === 60) {
                        return new Promise((resolve) => {
                            mockTimeout = setTimeout(() => {
                                resolve([]);
                            }, 1000);
                        });
                    }

                    return [];
                });

            fireEvent.click(await screen.findByRole('button', { name: 'Play video' }));

            // By default we play 1 frame per second
            act(() => {
                jest.advanceTimersByTime(1000);
            });

            await waitFor(() => {
                expect(annotationService.getAnnotations).toHaveBeenCalledWith(
                    mockedDatasetIdentifier,
                    expect.anything(),
                    getVideoFrame(60)
                );
            });

            act(() => {
                jest.advanceTimersByTime(1000);
            });

            await waitFor(() => {
                expect(annotationService.getAnnotations).toHaveBeenCalledWith(
                    mockedDatasetIdentifier,
                    expect.anything(),
                    getVideoFrame(120)
                );
            });

            const pauseButton = screen.getByRole('button', { name: 'Pause video' });
            fireEvent.click(pauseButton);
            expect(await screen.findByRole('button', { name: 'Play video' })).toBeInTheDocument();

            spy.mockRestore();

            if (mockTimeout) {
                clearTimeout(mockTimeout);
            }
        });

        it('Stops playing when manually changing a frame', async () => {
            await renderVideoPlayer(
                getMockedVideoFrameMediaItem({
                    identifier: {
                        videoId: 'test-video',
                        frameNumber: 120,
                        type: MEDIA_TYPE.VIDEO_FRAME,
                    },
                })
            );

            fireEvent.click(await screen.findByRole('button', { name: 'Play video' }));
            fireEvent.click(screen.getByRole('button', { name: 'Go to next frame' }));
            expect(screen.getByRole('button', { name: 'Play video' })).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: 'Play video' }));
            fireEvent.click(screen.getByRole('button', { name: 'Go to previous frame' }));
            expect(screen.getByRole('button', { name: 'Play video' })).toBeInTheDocument();
        });
    });

    describe('Video player in active mode', () => {
        it('does not switch to a different video frame when selecting a different task', async () => {
            const annotationService = createInMemoryAnnotationService();
            const mediaService = createInMemoryMediaService();
            const projectService = createInMemoryProjectService();
            projectService.getProject = async () => {
                return getMockedProject({
                    tasks: [
                        getMockedTask({
                            id: 'detection-task',
                            domain: DOMAIN.DETECTION,
                            title: 'Detection',
                        }),
                        getMockedTask({
                            id: 'segmentation-task',
                            domain: DOMAIN.SEGMENTATION,
                            title: 'Segmentation',
                        }),
                    ],
                });
            };

            const videoFrames = [
                videoFrame,
                getMockedVideoFrameMediaItem({
                    identifier: { ...videoFrame.identifier, frameNumber: videoFrame.identifier.frameNumber + 60 },
                }),
                getMockedVideoFrameMediaItem({
                    identifier: { ...videoFrame.identifier, frameNumber: videoFrame.identifier.frameNumber + 120 },
                }),
            ];

            mediaService.getActiveMedia = jest
                .fn()
                .mockImplementation((_dataset: DatasetIdentifier, _mediaItemsLoadSize: number, taskId?: string) => {
                    return {
                        nextPage: '',
                        media: taskId === undefined ? videoFrames : [videoFrames[1], videoFrames[2]],
                        mediaCount: { images: 10, videos: 10 },
                    };
                });

            const selectVideoFrame = jest.fn();
            const ChangeTask = () => {
                const { setSelectedTask, tasks } = useTask();
                const { activeMediaItemsQuery } = useDataset();

                return (
                    <>
                        {activeMediaItemsQuery.isPending ? <div role='progressbar'>Loading</div> : <></>}
                        <ul>
                            <li>
                                <button onClick={() => setSelectedTask(null)}>All tasks</button>
                            </li>
                            {tasks.map((task) => (
                                <li key={task.id}>
                                    <button onClick={() => setSelectedTask(task)}>{task.title}</button>
                                </li>
                            ))}
                        </ul>
                    </>
                );
            };

            await render(
                <VideoPlayerProvider videoFrame={videoFrame} selectVideoFrame={selectVideoFrame}>
                    <VideoPlayer />
                    <ChangeTask />
                </VideoPlayerProvider>,
                {
                    datasetIdentifier: mockedDatasetIdentifier,
                    services: { annotationService, mediaService, projectService },
                }
            );

            const slider = await screen.findByRole('slider');
            expect(slider).toHaveAttribute('value', '0');

            expect(mediaService.getActiveMedia).toHaveBeenCalledWith(mockedDatasetIdentifier, 50, undefined);
            expect(selectVideoFrame).not.toHaveBeenCalled();

            // Switching to a different task should not change the video frame,
            // even if the active set does not contain the current video frame
            fireEvent.click(screen.getByRole('button', { name: /Detection/i }));
            await waitForElementToBeRemoved(screen.getByRole('progressbar'));
            expect(mediaService.getActiveMedia).toHaveBeenCalledWith(mockedDatasetIdentifier, 50, 'detection-task');
            expect(selectVideoFrame).not.toHaveBeenCalled();

            fireEvent.click(screen.getByRole('button', { name: /Segmentation/i }));
            await waitForElementToBeRemoved(screen.getByRole('progressbar'));
            expect(mediaService.getActiveMedia).toHaveBeenCalledWith(mockedDatasetIdentifier, 50, 'segmentation-task');
            expect(selectVideoFrame).not.toHaveBeenCalled();
            expect(slider).toHaveAttribute('value', '0');
        });

        it('does not allow using active frames in an anomaly task', async () => {
            const annotationService = createInMemoryAnnotationService();
            const mediaService = createInMemoryMediaService();
            const projectService = createInMemoryProjectService();
            projectService.getProject = async () => {
                return getMockedProject({
                    tasks: [
                        getMockedTask({
                            id: 'anomaly-task',
                            domain: DOMAIN.ANOMALY_CLASSIFICATION,
                            title: 'Anomaly classification',
                        }),
                    ],
                });
            };

            const selectVideoFrame = jest.fn();

            await render(
                <VideoPlayerProvider videoFrame={videoFrame} selectVideoFrame={selectVideoFrame}>
                    <VideoPlayer />
                </VideoPlayerProvider>,
                {
                    datasetIdentifier: mockedDatasetIdentifier,
                    services: { annotationService, mediaService, projectService },
                }
            );

            expect(await screen.findByRole('slider')).toBeInTheDocument();

            expect(screen.queryByRole('switch', { name: 'Active frames' })).not.toBeInTheDocument();
        });
    });

    it('resets the frameskip when switching to a different video', async () => {
        const otherVideo = {
            ...videoFrame,
            identifier: { ...videoFrame.identifier, videoId: 'other-video-id' },
            metadata: { ...videoFrame.metadata, frameStride: 20 },
        };

        const AppThatChangesSelectedVideo = () => {
            const [selectedVideoFrame, setVideoFrame] = useState(videoFrame);
            const handleOnClick = () => {
                setVideoFrame(otherVideo);
            };

            return (
                <VideoPlayerProvider videoFrame={selectedVideoFrame} selectVideoFrame={jest.fn()}>
                    <VideoPlayer />
                    <button onClick={handleOnClick}>Change video</button>
                </VideoPlayerProvider>
            );
        };

        await render(<AppThatChangesSelectedVideo />);

        const slider = await screen.findByRole('slider');
        expect(slider).toHaveAttribute('step', '60');

        fireEvent.click(screen.getByRole('button', { name: /Change video/i }));
        expect(slider).toHaveAttribute('step', '20');
    });
});
