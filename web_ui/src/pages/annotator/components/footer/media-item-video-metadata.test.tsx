// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { getMockedVideoFrameMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { MediaItemVideoMetadata } from './media-item-video-metadata.component';

describe('Footer/Media item video metadata', () => {
    it('Show footer of selected frame from video', () => {
        const mockedVideoFrameItem = getMockedVideoFrameMediaItem({
            name: 'Test 1',
            identifier: { videoId: 'test-video-id', type: MEDIA_TYPE.VIDEO_FRAME, frameNumber: 6 },
            metadata: {
                duration: NaN,
                height: 300,
                width: 500,
                frames: NaN,
                size: 1024,
                fps: NaN,
                frameStride: NaN,
            },
        });

        render(<MediaItemVideoMetadata mediaItem={mockedVideoFrameItem} />);

        expect(screen.queryByLabelText('last annotator')).not.toBeInTheDocument();
        expect(screen.getByLabelText('media name')).toHaveTextContent('Test 1 (500 px x 300 px)');
        expect(screen.queryByLabelText('fps')).not.toBeInTheDocument();
        expect(screen.getByLabelText('frame number')).toHaveTextContent('6F');
    });

    it('Show footer of video frame selected item', () => {
        const mockedVideoFrameItem = getMockedVideoFrameMediaItem({
            name: 'Test 1',
            identifier: { videoId: 'test-video-id', type: MEDIA_TYPE.VIDEO_FRAME, frameNumber: 6 },
            metadata: {
                duration: 10,
                height: 300,
                width: 500,
                frames: 20,
                size: 1024,
                fps: 2,
                frameStride: 2,
            },
            lastAnnotatorId: 'test@intel.com',
        });

        render(<MediaItemVideoMetadata mediaItem={mockedVideoFrameItem} />);

        expect(screen.getByLabelText('last annotator')).toHaveTextContent('Last annotator: test@intel.com');
        expect(screen.getByLabelText('media name')).toHaveTextContent('Test 1 (500 px x 300 px)');
        expect(screen.getByLabelText('fps')).toHaveTextContent('2.00 fps');
        expect(screen.getByLabelText('frame number')).toHaveTextContent('6F');
    });
});
