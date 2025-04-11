// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MEDIA_TYPE } from './base-media.interface';
import { MediaIdentifier, mediaIdentifierToString } from './media.interface';
import { VideoFrameIdentifier, VideoIdentifier } from './video.interface';

describe('mediaIdentifierToString', () => {
    const imageIdentifier: MediaIdentifier = {
        type: MEDIA_TYPE.IMAGE,
        imageId: '123-image',
    };
    const videoIdentifier: VideoIdentifier = {
        type: MEDIA_TYPE.VIDEO,
        videoId: '123-video',
    };
    const videoFrameIdentifier: VideoFrameIdentifier = {
        type: MEDIA_TYPE.VIDEO_FRAME,
        videoId: '123-video',
        frameNumber: 10,
    };

    test.each([
        [imageIdentifier, 'image-123-image'],
        [videoIdentifier, 'video-123-video'],
        [videoFrameIdentifier, 'videoframe-123-video-10'],
    ])('converts %o to %o', (identifier, expected): void => {
        expect(mediaIdentifierToString(identifier)).toBe(expected);
    });
});
