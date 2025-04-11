// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { MEDIA_ANNOTATION_STATUS } from '../../../core/media/base.interface';
import { MediaItem } from '../../../core/media/media.interface';
import {
    getMockedImageMediaItem,
    getMockedVideoFrameMediaItem,
    getMockedVideoMediaItem,
} from '../../../test-utils/mocked-items-factory/mocked-media';
import { projectRender as render } from '../../../test-utils/project-provider-render';
import { MediaItemView } from './media-item-view.component';

describe('MediaItemView', () => {
    const imageMediaItem = getMockedImageMediaItem({
        annotationStatePerTask: [{ taskId: 'task-id', state: MEDIA_ANNOTATION_STATUS.ANNOTATED }],
    });

    const renderMedia = async (
        mediaItem: MediaItem = imageMediaItem,
        shouldShowAnnotationIndicator = true,
        shouldShowVideoIndicator = true
    ) => {
        await render(
            <MediaItemView
                mediaItem={mediaItem}
                shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                shouldShowVideoIndicator={shouldShowVideoIndicator}
            />
        );
    };

    it('should display media item placeholder when media item is loading for some time', async () => {
        await renderMedia();

        await waitFor(() => {
            expect(screen.getByTestId('image-placeholder-id')).toBeInTheDocument();
        });
    });

    it('should not display media item placeholder when media item is loading', async () => {
        await renderMedia();

        fireEvent.load(screen.getByAltText(imageMediaItem.name));

        await waitFor(() => {
            expect(screen.queryByTestId('image-placeholder-id')).not.toBeInTheDocument();
        });
    });

    it("should display duration indicator and shouldn't show frames indicator for video media item", async () => {
        const videoMediaItem = getMockedVideoMediaItem({});

        await renderMedia(videoMediaItem);

        expect(screen.queryByTestId('video-indicator-frames-id')).not.toBeInTheDocument();
        expect(screen.getByTestId('video-indicator-duration-id')).toBeInTheDocument();
    });

    it('should display video indicator (duration, frames) for video media item', async () => {
        const videoMediaItem = getMockedVideoMediaItem({ matchedFrames: 20 });

        await renderMedia(videoMediaItem);

        expect(screen.getByTestId('video-indicator-frames-id')).toBeInTheDocument();
        expect(screen.getByTestId('video-indicator-duration-id')).toBeInTheDocument();
    });

    it('should display video frame indicator (frame) for video media item', async () => {
        const videoFrameMediaItem = getMockedVideoFrameMediaItem({});

        await renderMedia(videoFrameMediaItem);

        expect(screen.getByTestId('video-frame-indicator-id')).toBeInTheDocument();
    });

    it('should not display video frame indicator (frame) for video media item when it is turned off', async () => {
        const videoFrameMediaItem = getMockedVideoFrameMediaItem({});

        await renderMedia(videoFrameMediaItem, true, false);

        expect(screen.queryByTestId('video-frame-indicator-id')).not.toBeInTheDocument();
    });

    it('should display annotation state indicator', async () => {
        await renderMedia();

        expect(screen.getByTestId('annotation-state-indicator-id')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /annotated/i })).toBeInTheDocument();
    });

    it('should not display annotation state indicator', async () => {
        await renderMedia(imageMediaItem, false);

        expect(screen.queryByTestId('annotation-state-indicator-id')).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /annotated/i })).not.toBeInTheDocument();
    });

    it('should not display annotation state indicator for videos if it does not contain statistics', async () => {
        const videoMediaItem = getMockedVideoMediaItem({
            annotationStatistics: {
                annotated: 0,
                partiallyAnnotated: 0,
                unannotated: 0,
            },
        });

        await renderMedia(videoMediaItem, true);

        expect(screen.queryByTestId('annotation-state-indicator-id')).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /annotated/i })).not.toBeInTheDocument();
    });

    it('should display annotation state indicator for videos if it contains statistics', async () => {
        const videoMediaItem = getMockedVideoMediaItem({
            annotationStatistics: {
                annotated: 3,
                partiallyAnnotated: 0,
                unannotated: 0,
            },
        });

        await renderMedia(videoMediaItem, true);

        expect(screen.queryByTestId('annotation-state-indicator-id')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'annotation state indicator' })).toBeInTheDocument();
    });
});
