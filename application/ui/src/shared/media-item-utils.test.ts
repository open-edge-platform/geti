// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MediaOmePlane } from '@/api/types';
import { getMockedMediaImage, getMockedVideo, getMockedVideoFrame } from 'mocks/mock-media';

import {
    getMediaItemImageUrl,
    getMediaItemKey,
    getMediaItemPredictionRange,
    getMediaItemQueryParams,
    isAnnotatableMedia,
} from './media-item-utils';
import { getMediaBinaryUrl, getOmeRenderUrl } from './media-url.utils';

const image = getMockedMediaImage({ id: 'image-1' });
const video = getMockedVideo({ id: 'video-1' });
const videoFrame = getMockedVideoFrame({ id: 'video-1', frame_number: 7, frame_stride: 30 });

describe('media-item utils', () => {
    it.each([
        { name: 'image', media: image, expected: true },
        { name: 'video frame', media: videoFrame, expected: true },
        { name: 'video', media: video, expected: false },
        { name: 'undefined', media: undefined, expected: false },
    ])('isAnnotatableMedia is $expected for $name', ({ media, expected }) => {
        expect(isAnnotatableMedia(media)).toBe(expected);
    });
    describe.each([
        { name: 'image', media: image },
        { name: 'video', media: video },
    ])('for a media item addressed by id only ($name)', ({ media }) => {
        it('builds every address from the id', () => {
            expect(getMediaItemKey(media)).toBe(media.id);
            expect(getMediaItemQueryParams(media)).toBeUndefined();
            expect(getMediaItemImageUrl('p1', media)).toBe(getMediaBinaryUrl('p1', media.id));
            expect(getMediaItemPredictionRange(media)).toBeNull();
        });
    });

    describe('for a video frame', () => {
        it('addresses the item by its id and frame number', () => {
            expect(getMediaItemKey(videoFrame)).toBe('video-1-7');
            expect(getMediaItemQueryParams(videoFrame)).toEqual({ frame_index: 7 });
            expect(getMediaItemImageUrl('p1', videoFrame)).toBe(`${getMediaBinaryUrl('p1', 'video-1')}?frame_index=7`);
            expect(getMediaItemPredictionRange(videoFrame)).toEqual({ start_frame: 7, end_frame: 7, stride: 30 });
        });
    });

    describe('for an OME plane', () => {
        const plane: MediaOmePlane = {
            ...getMockedMediaImage({ id: 'ome-1' }),
            type: 'ome_plane',
            size_z: 10,
            size_c: 3,
            size_t: 5,
            z_index: 4,
            t_index: 2,
            channels: [],
        };

        it('addresses the item by its id and (Z, T), and shows a render of it', () => {
            expect(getMediaItemKey(plane)).toBe('ome-1-z4-t2');
            expect(getMediaItemQueryParams(plane)).toEqual({ z: 4, t: 2 });
            expect(getMediaItemImageUrl('p1', plane)).toBe(getOmeRenderUrl('p1', plane));
        });
    });
});
