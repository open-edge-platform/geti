// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getMockedVideo } from 'mocks/mock-media';
import { renderHook } from 'test-utils/render';

import { SelectedMediaItemProvider, useSelectedMediaItem } from './selected-media-item-provider.component';

rs.mock('./hooks/use-load-image-query.hook', () => ({
    useLoadImageQuery: () => ({ data: undefined }),
}));

describe('SelectedMediaItemProvider', () => {
    it.each([
        [30000 / 1001, 30],
        [24.25, 24],
        [24.5, 25],
        [0.4, 1],
        [25, 25],
    ])('preserves %s fps and rounds the frame stride to %s', (fps, expectedFrameStride) => {
        const video = getMockedVideo({ fps });
        const { result } = renderHook(useSelectedMediaItem, {
            wrapper: ({ children }) => (
                <SelectedMediaItemProvider mediaItem={video}>{children}</SelectedMediaItemProvider>
            ),
        });

        expect(result.current.mediaItem).toMatchObject({
            type: 'video_frame',
            fps,
            frame_number: 0,
        });
        expect(result.current.mediaItem).toHaveProperty('frame_stride', expectedFrameStride);
    });
});
