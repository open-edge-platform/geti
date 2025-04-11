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
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { DatasetProvider } from '../../providers/dataset-provider/dataset-provider.component';
import { PreviousMediaItemButton } from './previous-media-item-button.component';

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

describe('Previous media item button', () => {
    afterAll(() => {
        jest.clearAllMocks();
    });

    it('Selects the previous media item from the dataset', async () => {
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
                <PreviousMediaItemButton selectMediaItem={selectMediaItem} selectedMediaItem={mediaItem} />
            </DatasetProvider>,
            { services: { mediaService } }
        );

        const btn = await screen.findByRole('button');
        await waitFor(() => {
            expect(btn).toBeEnabled();
        });

        fireEvent.click(btn);

        expect(selectMediaItem).toHaveBeenCalledWith(items[0]);
    });

    it('Is disabled when there is no previous media item', async () => {
        const items = [
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-1', type: MEDIA_TYPE.IMAGE } }),
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-2', type: MEDIA_TYPE.IMAGE } }),
            getMockedImageMediaItem({ identifier: { imageId: 'test-image-3', type: MEDIA_TYPE.IMAGE } }),
        ];
        const mediaItem = items[0];
        const mediaService = createInMemoryMediaService(items);

        render(
            <DatasetProvider>
                <PreviousMediaItemButton selectMediaItem={jest.fn()} selectedMediaItem={mediaItem} />
            </DatasetProvider>,
            { services: { mediaService } }
        );

        expect(screen.getByRole('button')).toBeDisabled();
    });
});
