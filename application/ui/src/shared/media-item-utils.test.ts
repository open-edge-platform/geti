// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getMockedMediaImage, getMockedVideo, getMockedVideoFrame } from 'mocks/mock-media';

import {
    getMediaItemBinaryUrl,
    getMediaItemKey,
    getMediaItemPredictionRange,
    getMediaItemQueryParams,
} from './media-item-utils';
import { getMediaBinaryUrl } from './media-url.utils';

const image = getMockedMediaImage({ id: 'image-1' });
const video = getMockedVideo({ id: 'video-1' });
const videoFrame = getMockedVideoFrame({ id: 'video-1', frame_number: 7, frame_stride: 30 });

describe('media-item utils', () => {
    describe.each([
        { name: 'image', media: image },
        { name: 'video', media: video },
    ])('for a media item addressed by id only ($name)', ({ media }) => {
        it('builds every address from the id', () => {
            expect(getMediaItemKey(media)).toBe(media.id);
            expect(getMediaItemQueryParams(media)).toBeUndefined();
            expect(getMediaItemBinaryUrl('p1', media)).toBe(getMediaBinaryUrl('p1', media.id));
            expect(getMediaItemPredictionRange(media)).toBeNull();
        });
    });

    describe('for a video frame', () => {
        it('addresses the item by its id and frame number', () => {
            expect(getMediaItemKey(videoFrame)).toBe('video-1-7');
            expect(getMediaItemQueryParams(videoFrame)).toEqual({ frame_index: 7 });
            expect(getMediaItemBinaryUrl('p1', videoFrame)).toBe(`${getMediaBinaryUrl('p1', 'video-1')}?frame_index=7`);
            expect(getMediaItemPredictionRange(videoFrame)).toEqual({ start_frame: 7, end_frame: 7, stride: 30 });
        });
    });
});
