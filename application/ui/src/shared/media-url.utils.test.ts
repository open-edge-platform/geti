// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
    getDatasetRevisionThumbnailUrl,
    getMediaBinaryUrl,
    getMediaDownloadUrl,
    getOmeRenderUrl,
    getProjectThumbnailUrl,
    getThumbnailUrl,
    getVideoFrameThumbnailUrl,
} from './media-url.utils';

const mocks = rs.hoisted(() => ({ apiBaseUrl: '' }));

rs.mock('../api/client', () => ({
    get API_BASE_URL() {
        return mocks.apiBaseUrl;
    },
}));

describe.each([
    { name: 'absolute base (dev/preview)', base: 'http://localhost:7860', prefix: 'http://localhost:7860' },
    { name: 'absolute base with trailing slash', base: 'http://localhost:7860/', prefix: 'http://localhost:7860' },
    { name: 'empty base (Docker, same origin)', base: '', prefix: '' },
])('media-url helpers with $name', ({ base, prefix }) => {
    beforeEach(() => {
        mocks.apiBaseUrl = base;
    });

    it('builds the expected URLs', () => {
        expect(getProjectThumbnailUrl('p1')).toBe(`${prefix}/api/projects/p1/thumbnail`);
        expect(getThumbnailUrl('p1', 'm1')).toBe(`${prefix}/api/projects/p1/dataset/media/m1/thumbnail`);
        expect(getMediaBinaryUrl('p1', 'm1')).toBe(`${prefix}/api/projects/p1/dataset/media/m1/binary`);
        expect(getMediaDownloadUrl('p1', 'm1')).toBe(`${prefix}/api/projects/p1/dataset/media/m1/binary?raw=true`);
        expect(getDatasetRevisionThumbnailUrl('p1', 'r1', 'm1')).toBe(
            `${prefix}/api/projects/p1/dataset_revisions/r1/items/m1/thumbnail`
        );
        expect(getVideoFrameThumbnailUrl('p1', 'm1', 7)).toBe(
            `${prefix}/api/projects/p1/dataset/media/m1/thumbnail?frame_index=7`
        );
    });
});

describe('getOmeRenderUrl', () => {
    const plane = { id: 'm1', z_index: 12, t_index: 3 };

    it('lists the shown channels in `c`, rounded, as uppercase hex without #', () => {
        const url = getOmeRenderUrl('p1', {
            ...plane,
            channels: [
                { channel: 0, enabled: true, color: '#3b6cff', window_min: 120.4, window_max: 2400.6 },
                { channel: 1, enabled: false, color: '#27C46A', window_min: 300, window_max: 9800 },
                { channel: 2, enabled: true, color: '#E8503A', window_min: 40, window_max: 1500 },
            ],
        });
        const { pathname, searchParams } = new URL(url, 'http://localhost');

        expect(pathname).toBe('/api/projects/p1/dataset/media/m1/render');
        expect(searchParams.get('z')).toBe('12');
        expect(searchParams.get('t')).toBe('3');
        expect(searchParams.get('c')).toBe('0|120:2401$3B6CFF,2|40:1500$E8503A');
    });

    it('sends an empty `c` when every channel is hidden', () => {
        const url = getOmeRenderUrl('p1', {
            ...plane,
            channels: [{ channel: 0, enabled: false, color: '#3B6CFF', window_min: 0, window_max: 1 }],
        });

        expect(new URL(url, 'http://localhost').searchParams.get('c')).toBe('');
    });

    it('omits `c` without a channel view, so the stored one is used', () => {
        const url = getOmeRenderUrl('p1', { ...plane, channels: [] });

        expect(new URL(url, 'http://localhost').searchParams.has('c')).toBe(false);
    });
});
