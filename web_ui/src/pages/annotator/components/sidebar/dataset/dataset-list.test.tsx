// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { createInMemoryMediaService } from '../../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { ViewModes } from '../../../../../shared/components/media-view-modes/utils';
import {
    getMockedImageMediaItem,
    getMockedVideoFrameMediaItem,
    getMockedVideoMediaItem,
} from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { annotatorRender as render } from '../../../test-utils/annotator-render';

import './../../../../../test-utils/mock-resize-observer';

import { AnnotatorDatasetList } from './annotator-dataset-list.component';

describe('AnnotatorDatasetList', () => {
    const mediaService = createInMemoryMediaService([
        getMockedImageMediaItem({ identifier: { type: MEDIA_TYPE.IMAGE, imageId: 'image-1' } }),
        getMockedImageMediaItem({ identifier: { type: MEDIA_TYPE.IMAGE, imageId: 'image-2' } }),
        getMockedImageMediaItem({ identifier: { type: MEDIA_TYPE.IMAGE, imageId: 'image-3' } }),
        getMockedVideoMediaItem({ identifier: { type: MEDIA_TYPE.VIDEO, videoId: 'video-1' } }),
        getMockedVideoFrameMediaItem({
            identifier: { type: MEDIA_TYPE.VIDEO_FRAME, videoId: 'video-1', frameNumber: 1 },
        }),
        getMockedVideoFrameMediaItem({
            identifier: { type: MEDIA_TYPE.VIDEO_FRAME, videoId: 'video-1', frameNumber: 2 },
        }),
    ]);

    it('groups video frames into 1 video thumbnail', async () => {
        await render(<AnnotatorDatasetList viewMode={ViewModes.SMALL} />, {
            services: { mediaService },
        });

        await waitFor(() => expect(screen.getAllByTestId('image-placeholder-id')).toHaveLength(4), { timeout: 10000 });
    });
});
