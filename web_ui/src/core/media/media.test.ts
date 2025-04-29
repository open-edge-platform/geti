// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
