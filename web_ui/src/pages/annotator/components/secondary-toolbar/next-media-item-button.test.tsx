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

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { createInMemoryMediaService } from '../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import {
    getMockedImageMediaItem,
    getMockedVideoFrameMediaItem,
} from '../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { DatasetProvider } from '../../providers/dataset-provider/dataset-provider.component';
import { useVideoPlayerContext } from '../video-player/video-player-provider.component';
import { NextMediaItemButton } from './next-media-item-button.component';

jest.mock('../video-player/video-player-provider.component', () => ({
    useVideoPlayerContext: jest.fn(),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../providers/task-chain-provider/task-chain-provider.component', () => ({
    useTaskChain: jest.fn(() => ({
        inputs: [],
    })),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    useTask: jest.fn(() => ({
        selectedTask: null,
    })),
}));

jest.mock('../../hooks/use-annotator-scene-interaction-state.hook', () => ({
    useIsSceneBusy: jest.fn(() => false),
}));

const datasetIdentifier = {
    workspaceId: 'workspace-id',
    projectId: 'project-id',
    datasetId: 'dataset-id',
};

jest.mock('../../hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: () => datasetIdentifier,
}));

describe('Next media item button', () => {
    beforeEach(() => {
        jest.mocked(useVideoPlayerContext).mockImplementation(() => undefined);
    });

    it('Selects the next media item from the dataset', async () => {
        const items = [
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-1', type: MEDIA_TYPE.IMAGE } }),
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-2', type: MEDIA_TYPE.IMAGE } }),
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-3', type: MEDIA_TYPE.IMAGE } }),
        ];
        const mediaItem = items[1];
        const mediaService = createInMemoryMediaService(items);

        const selectMediaItem = jest.fn();

        render(
            <DatasetProvider>
                <NextMediaItemButton selectMediaItem={selectMediaItem} selectedMediaItem={mediaItem} />
            </DatasetProvider>,
            {
                services: {
                    mediaService,
                },
            }
        );

        const btn = screen.getByRole('button');
        await waitFor(() => {
            expect(btn).toBeEnabled();
        });
        fireEvent.click(btn);

        expect(selectMediaItem).toHaveBeenCalledWith(items[2]);
    });

    it('Selects the next media item from the dataset when there is no next video frame', async () => {
        const videoFrame = getMockedVideoFrameMediaItem({
            identifier: { videoId: 'test-video-1', type: MEDIA_TYPE.VIDEO_FRAME, frameNumber: 600 },
        });

        // Return only the selected video frame so that submit must select a next media item
        (useVideoPlayerContext as jest.Mock).mockImplementation(() => {
            return { videoFrame, step: 60 };
        });

        const items = [
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-1', type: MEDIA_TYPE.IMAGE } }),
            { ...videoFrame, metadata: { ...videoFrame.metadata, frames: 600 } },
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-2', type: MEDIA_TYPE.IMAGE } }),
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-3', type: MEDIA_TYPE.IMAGE } }),
        ];
        const mediaItem = items[1];
        const mediaService = createInMemoryMediaService(items);

        const selectMediaItem = jest.fn();

        render(
            <DatasetProvider>
                <NextMediaItemButton selectMediaItem={selectMediaItem} selectedMediaItem={mediaItem} />
            </DatasetProvider>,
            {
                services: {
                    mediaService,
                },
            }
        );

        const btn = screen.getByRole('button');
        await waitFor(() => {
            expect(btn).toBeEnabled();
        });
        fireEvent.click(btn);

        expect(selectMediaItem).toHaveBeenCalledWith(items[2]);
    });

    it('Is disabled when there is no next media item', async () => {
        const items = [
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-1', type: MEDIA_TYPE.IMAGE } }),
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-2', type: MEDIA_TYPE.IMAGE } }),
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-3', type: MEDIA_TYPE.IMAGE } }),
        ];
        const mediaItem = items[2];
        const mediaService = createInMemoryMediaService(items);

        render(
            <DatasetProvider>
                <NextMediaItemButton selectMediaItem={jest.fn()} selectedMediaItem={mediaItem} />
            </DatasetProvider>,
            {
                services: {
                    mediaService,
                },
            }
        );

        expect(screen.getByRole('button')).toBeDisabled();
    });
});
