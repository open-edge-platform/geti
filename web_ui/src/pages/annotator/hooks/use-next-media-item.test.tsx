// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../core/media/base-media.interface';
import { MediaItem } from '../../../core/media/media.interface';
import { createInMemoryMediaService } from '../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { MediaService } from '../../../core/media/services/media-service.interface';
import { VideoFrame } from '../../../core/media/video.interface';
import { useFilterSearchParam } from '../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import {
    getMockedImageMediaItem,
    getMockedVideoFrameMediaItem,
    getMockedVideoMediaItem,
} from '../../../test-utils/mocked-items-factory/mocked-media';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { getMockedVideoControls } from '../components/video-player/video-controls/test-utils';
import { useVideoPlayerContext } from '../components/video-player/video-player-provider.component';
import { DatasetProvider } from '../providers/dataset-provider/dataset-provider.component';
import { findIndex } from '../utils';
import { useNextMediaItem } from './use-next-media-item.hook';

jest.mock('../providers/task-provider/task-provider.component', () => ({
    useTask: jest.fn(() => ({
        selectedTask: null,
    })),
}));

jest.mock('../providers/task-chain-provider/task-chain-provider.component', () => ({
    useTaskChain: jest.fn(() => ({
        inputs: [],
    })),
}));

jest.mock('./use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: () => ({
        workspaceId: 'workspace-id',
        projectId: 'project-id',
        datasetId: 'dataset-id',
        organizationId: 'organization-id',
    }),
}));

jest.mock('../../../hooks/use-filter-search-param/use-filter-search-param.hook', () => ({
    ...jest.requireActual('../../../hooks/use-filter-search-param/use-filter-search-param.hook'),
    useFilterSearchParam: jest.fn(() => []),
}));

const getMockedMediaItem = (index = 0): MediaItem => {
    return getMockedImageMediaItem({ identifier: { type: MEDIA_TYPE.IMAGE, imageId: `${index}` } });
};

const Providers = ({
    children,
    mediaService,
    activeSetMode = false,
}: {
    children: ReactNode;
    mediaService: MediaService;
    activeSetMode?: boolean;
}) => {
    return (
        <RequiredProviders
            useInMemoryEnvironment
            mediaService={mediaService}
            initialEntries={activeSetMode ? ['?active=true'] : undefined}
        >
            <DatasetProvider>{children}</DatasetProvider>
        </RequiredProviders>
    );
};

jest.mock('../components/video-player/video-player-provider.component');

describe('useNextMediaItem', () => {
    beforeEach(() => {
        jest.mocked(useFilterSearchParam).mockReturnValue([[], jest.fn()]);
    });

    it('Returns the next media item based on the given filter', async () => {
        const items = [getMockedMediaItem(0), getMockedMediaItem(1), getMockedMediaItem(2), getMockedMediaItem(3)];
        const mediaService = createInMemoryMediaService(items);

        const mediaItem = getMockedImageMediaItem({});
        const filter = jest.fn((_, mediaItems) => {
            return { type: 'media' as const, media: mediaItems[0] };
        });

        const wrapper = ({ children }: { children: ReactNode }) => (
            <Providers mediaService={mediaService}>{children}</Providers>
        );
        const { result } = renderHook(() => useNextMediaItem(mediaItem, filter), { wrapper });

        await waitFor(() => {
            expect(filter).toBeCalledWith(mediaItem, items);
            expect(result.current).toEqual({ type: 'media', media: items[0] });
        });
    });

    describe('Selecting next video frame based on the available video frames', () => {
        const items = [
            getMockedMediaItem(0),
            getMockedVideoFrameMediaItem({
                identifier: { videoId: 'test-video', frameNumber: 0, type: MEDIA_TYPE.VIDEO_FRAME },
            }),
            getMockedVideoFrameMediaItem({
                identifier: { videoId: 'test-video', frameNumber: 60, type: MEDIA_TYPE.VIDEO_FRAME },
            }),
            getMockedVideoFrameMediaItem({
                identifier: { videoId: 'test-video', frameNumber: 120, type: MEDIA_TYPE.VIDEO_FRAME },
            }),
            getMockedMediaItem(1),
            getMockedMediaItem(2),
            getMockedMediaItem(3),
        ];

        beforeEach(() => {
            jest.mocked(useVideoPlayerContext).mockImplementation(() => {
                return {
                    videoFrame: items[1] as VideoFrame,
                    setStep: jest.fn(),
                    step: 60,
                    videoControls: getMockedVideoControls({}),
                };
            });
        });

        it('Does not have filtered videos', async () => {
            const videoFrames = [0, 60, 120, 180, 240, 300, 360, 420, 480, 540];

            const mediaService = createInMemoryMediaService(items);

            const mediaItem = items[1];
            const filter = jest.fn((_, mediaItems) => {
                return { type: 'media' as const, media: mediaItems[1] };
            });

            const wrapper = ({ children }: { children: ReactNode }) => (
                <Providers mediaService={mediaService}>{children}</Providers>
            );

            const videoFilter = jest.fn(
                (_, videoFrameNumbers) =>
                    ({
                        type: 'videoFrame',
                        frameNumber: videoFrameNumbers[1],
                    }) as const
            );
            const { result } = renderHook(() => useNextMediaItem(mediaItem, filter, videoFilter), {
                wrapper,
            });

            await waitFor(() => {
                expect(videoFilter).toBeCalledWith(mediaItem, videoFrames);
                expect(result.current).toEqual({ type: 'videoFrame', frameNumber: 60 });
            });
        });

        it('Has filtered videos', async () => {
            const filteredFrames = [0, 60, 120];
            const mediaItem = items[1];

            jest.mocked(useFilterSearchParam).mockReturnValue([{ condition: 'and', rules: [] }, jest.fn()]);

            const mediaService = createInMemoryMediaService(items);
            // @ts-expect-error meh
            mediaService.getAdvancedFramesFilter = async () => ({
                nextPage: undefined,
                videoFrames: [items[1], items[2], items[3]],
                totalMatchedVideoFrames: 3,
            });

            const filter = jest.fn((_, mediaItems) => {
                return { type: 'media' as const, media: mediaItems[1] };
            });

            const wrapper = ({ children }: { children: ReactNode }) => (
                <Providers mediaService={mediaService}>{children}</Providers>
            );
            const videoFilter = jest.fn(
                (_, videoFrameNumbers) =>
                    ({
                        type: 'videoFrame',
                        frameNumber: videoFrameNumbers[1],
                    }) as const
            );
            const { result } = renderHook(() => useNextMediaItem(mediaItem, filter, videoFilter), {
                wrapper,
            });

            await waitFor(() => {
                expect(videoFilter).toBeCalledWith(mediaItem, filteredFrames);
            });

            expect(result.current).toEqual({ type: 'videoFrame', frameNumber: 60 });
        });

        it('Active mode', async () => {
            const activeVideoFrames = [0, 30, 120];

            const mediaService = createInMemoryMediaService(items);
            mediaService.getActiveMedia = async () => {
                return {
                    nextPage: undefined,
                    media: activeVideoFrames.map((frameNumber) => {
                        return getMockedVideoFrameMediaItem({
                            identifier: { type: MEDIA_TYPE.VIDEO_FRAME, videoId: 'test-video', frameNumber },
                        });
                    }),
                    mediaCount: { images: 10, videos: 10 },
                };
            };

            const mediaItem = items[1];
            const filter = jest.fn((_, mediaItems) => {
                return { type: 'media' as const, media: mediaItems[1] };
            });

            const wrapper = ({ children }: { children: ReactNode }) => (
                <Providers activeSetMode mediaService={mediaService}>
                    {children}
                </Providers>
            );
            const videoFilter = jest.fn(
                (_, videoFrameNumbers) =>
                    ({
                        type: 'videoFrame',
                        frameNumber: videoFrameNumbers[1],
                    }) as const
            );
            const { result } = renderHook(() => useNextMediaItem(mediaItem, filter, videoFilter), {
                wrapper,
            });

            await waitFor(() => {
                expect(videoFilter).toBeCalledWith(mediaItem, activeVideoFrames);
            });

            expect(result.current).toEqual({ type: 'videoFrame', frameNumber: 30 });
        });
    });
});

describe('findIndex', () => {
    it('finds the index of a media item inside of set', () => {
        const items = [
            getMockedImageMediaItem({ identifier: { imageId: 'test-image', type: MEDIA_TYPE.IMAGE } }),
            getMockedVideoFrameMediaItem({
                identifier: { videoId: 'test-video', frameNumber: 0, type: MEDIA_TYPE.VIDEO_FRAME },
            }),
            getMockedVideoFrameMediaItem({
                identifier: { videoId: 'test-video', frameNumber: 60, type: MEDIA_TYPE.VIDEO_FRAME },
            }),
            getMockedVideoFrameMediaItem({
                identifier: { videoId: 'test-video', frameNumber: 120, type: MEDIA_TYPE.VIDEO_FRAME },
            }),
        ];

        expect(findIndex(items[2], items)).toEqual(2);
    });

    it("finds the index of a videoFrame's video inside of set", () => {
        const mediaItem = getMockedVideoFrameMediaItem({
            identifier: { videoId: 'test-video', frameNumber: 0, type: MEDIA_TYPE.VIDEO_FRAME },
        });

        const items = [
            getMockedImageMediaItem({ identifier: { imageId: 'test-image', type: MEDIA_TYPE.IMAGE } }),
            getMockedVideoMediaItem({
                identifier: { videoId: 'test-video', type: MEDIA_TYPE.VIDEO },
            }),
        ];

        expect(findIndex(mediaItem, items)).toEqual(1);
    });
});
