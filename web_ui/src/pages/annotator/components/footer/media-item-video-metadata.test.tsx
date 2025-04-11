// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
