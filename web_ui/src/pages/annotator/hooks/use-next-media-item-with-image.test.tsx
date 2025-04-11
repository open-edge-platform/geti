// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
} from '../../../test-utils/mocked-items-factory/mocked-media';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { getMockedImage } from '../../../test-utils/utils';
import { getMockedVideoControls } from '../components/video-player/video-controls/test-utils';
import { useVideoPlayerContext } from '../components/video-player/video-player-provider.component';
import { DatasetProvider } from '../providers/dataset-provider/dataset-provider.component';
import { DefaultSelectedMediaItemProvider } from '../providers/selected-media-item-provider/default-selected-media-item-provider.component';
import { useNextMediaItemWithImage } from './use-next-media-item-with-image.hook';

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

describe('useNextMediaItemWithImage', () => {
    beforeEach(() => {
        jest.mocked(useFilterSearchParam).mockReturnValue([[], jest.fn()]);
    });

    it('Does not load an image if the there is no selected media item', async () => {
        const items = [getMockedMediaItem(0), getMockedMediaItem(1), getMockedMediaItem(2), getMockedMediaItem(3)];
        const mediaService = createInMemoryMediaService(items);

        const selectedMediaItem = undefined;
        const wrapper = ({ children }: { children: ReactNode }) => (
            <Providers mediaService={mediaService}>
                <DefaultSelectedMediaItemProvider selectedMediaItem={selectedMediaItem}>
                    {children}
                </DefaultSelectedMediaItemProvider>
            </Providers>
        );

        const { result } = renderHook(() => useNextMediaItemWithImage(), { wrapper });

        expect(result.current).toBeUndefined();
    });

    it('Loads the image of the next image item', async () => {
        const items = [getMockedMediaItem(0), getMockedMediaItem(1), getMockedMediaItem(2), getMockedMediaItem(3)];
        const mediaService = createInMemoryMediaService(items);

        const selectedMediaItem = { ...items[0], image: getMockedImage(), annotations: [], predictions: undefined };

        const wrapper = ({ children }: { children: ReactNode }) => (
            <Providers mediaService={mediaService}>
                <DefaultSelectedMediaItemProvider selectedMediaItem={selectedMediaItem}>
                    {children}
                </DefaultSelectedMediaItemProvider>
            </Providers>
        );

        const { result } = renderHook(() => useNextMediaItemWithImage(), { wrapper });

        await waitFor(() => {
            expect(result.current?.image).not.toBeUndefined();
        });

        expect(result.current?.image).toBeInstanceOf(ImageData);
        expect(result.current?.identifier).toStrictEqual(items[1].identifier);
    });

    describe('A video frame is selected', () => {
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

        it('Loads the image of the next video frame', async () => {
            const mediaService = createInMemoryMediaService(items);

            const selectedMediaItem = { ...items[1], image: getMockedImage(), annotations: [], predictions: undefined };
            const wrapper = ({ children }: { children: ReactNode }) => (
                <Providers mediaService={mediaService}>
                    <DefaultSelectedMediaItemProvider selectedMediaItem={selectedMediaItem}>
                        {children}
                    </DefaultSelectedMediaItemProvider>
                </Providers>
            );

            const { result } = renderHook(() => useNextMediaItemWithImage(), { wrapper });

            await waitFor(() => {
                expect(result.current?.image).not.toBeUndefined();
            });

            expect(result.current?.image).toBeInstanceOf(ImageData);
            expect(result.current?.identifier).toStrictEqual(items[2].identifier);
        });
    });
});
