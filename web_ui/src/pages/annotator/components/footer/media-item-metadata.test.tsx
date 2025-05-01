// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import {
    getMockedImageMediaItem,
    getMockedVideoMediaItem,
} from '../../../../test-utils/mocked-items-factory/mocked-media';
import { MediaItemImageMetadata } from './media-item-image-metadata.component';
import { MediaItemVideoMetadata } from './media-item-video-metadata.component';

jest.mock('@shared/utils', () => ({
    ...jest.requireActual('../../utils'),
    trimText: jest.fn((text) => text),
}));

describe('Media item metadata', () => {
    describe('IMAGE metadata', () => {
        it("shows the media item's image size and name", () => {
            const name = 'test_name';
            const mediaItem = getMockedImageMediaItem({ metadata: { width: 200, height: 300, size: 12345 }, name });

            render(<MediaItemImageMetadata mediaItem={mediaItem} />);

            expect(screen.getByText(`${name} (200 px x 300 px)`)).toBeInTheDocument();
        });
    });

    describe('VIDEO metadata', () => {
        const duration = 33 * 3600 + 51 * 60 + 7;
        const frames = duration * 60;
        const fps = frames / duration;
        const metadata = { width: 200, height: 300, fps, frames, duration, frameStride: 60, size: 12345 };

        it('shows media name with resolution and fps', async () => {
            const name = 'dunkirk';
            const mediaItem = getMockedVideoMediaItem({ metadata, name });

            render(<MediaItemVideoMetadata mediaItem={mediaItem} />);

            expect(screen.getByText('dunkirk (200 px x 300 px)')).toBeInTheDocument();
            expect(screen.getByText('60.00 fps')).toBeInTheDocument();
        });

        it("shows a video's metadata correctly", async () => {
            const name = 'test_video_name';
            const mediaItem = getMockedVideoMediaItem({ metadata, name });

            render(<MediaItemVideoMetadata mediaItem={mediaItem} />);

            expect(screen.getByText(`${name} (200 px x 300 px)`)).toBeInTheDocument();
            expect(screen.getByText('60.00 fps')).toBeInTheDocument();
        });
    });
});
