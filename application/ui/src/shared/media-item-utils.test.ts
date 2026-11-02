// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getMockedMediaImage, getMockedOmePlane, getMockedVideo, getMockedVideoFrame } from 'mocks/mock-media';

import {
    getMediaItemBinaryUrl,
    getMediaItemKey,
    getMediaItemPredictionRange,
    getMediaItemQueryParams,
    isOmeMedia,
} from './media-item-utils';
import { getMediaBinaryUrl, getOmeRenderUrl } from './media-url.utils';

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

    describe('for an OME plane', () => {
        const omePlane = getMockedOmePlane({ z_index: 3, t_index: 1, render_level: 2, render_version: 'abc' });

        it('addresses the item by its id and plane coordinates', () => {
            expect(getMediaItemQueryParams(omePlane)).toEqual({ z: 3, t: 1 });
            expect(getMediaItemPredictionRange(omePlane)).toEqual({
                z: { start: 3, end: 3, stride: 1 },
                t: { start: 1, end: 1, stride: 1 },
            });
        });

        it('displays the plane rendered with its channel display settings', () => {
            expect(getMediaItemBinaryUrl('p1', omePlane)).toBe(
                getOmeRenderUrl('p1', 'ome-1', { z: 3, t: 1, level: 2, version: 'abc' })
            );
            expect(getMediaItemBinaryUrl('p1', omePlane)).toContain(
                '/dataset/media/ome-1/render?z=3&t=1&level=2&v=abc'
            );
        });

        it('changes key when the plane or its rendering changes', () => {
            const key = getMediaItemKey(omePlane);

            expect(getMediaItemKey({ ...omePlane, z_index: 4 })).not.toBe(key);
            expect(getMediaItemKey({ ...omePlane, render_version: 'def' })).not.toBe(key);
        });

        it('is recognised as OME media, like its OME image', () => {
            expect(isOmeMedia(omePlane)).toBe(true);
            expect(isOmeMedia({ type: 'ome_image' })).toBe(true);
            expect(isOmeMedia(image)).toBe(false);
        });
    });
});
