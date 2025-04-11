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

import { MEDIA_TYPE } from '../../core/media/base-media.interface';
import { MEDIA_ANNOTATION_STATUS } from '../../core/media/base.interface';
import { Image } from '../../core/media/image.interface';
import { Video, VideoFrame } from '../../core/media/video.interface';

export const getMockedImageMediaItem = (mediaItem: Partial<Image>): Image => {
    return {
        identifier: { type: MEDIA_TYPE.IMAGE, imageId: 'test-image' },
        name: 'Test image',
        status: MEDIA_ANNOTATION_STATUS.NONE,
        src: '',
        thumbnailSrc: '',
        metadata: { width: 100, height: 100, size: 696969 },
        annotationStatePerTask: [],
        uploadTime: '22 Jun 2022',
        uploaderId: '6b3b8453-92a2-41ef-9725-63badb218504',
        lastAnnotatorId: null,
        ...mediaItem,
    };
};

export const getMockedVideoMediaItem = (mediaItem: Partial<Video>): Video => {
    return {
        identifier: { type: MEDIA_TYPE.VIDEO, videoId: 'test-video' },
        name: 'Test video',
        status: MEDIA_ANNOTATION_STATUS.NONE,
        src: '',
        thumbnailSrc: '',
        metadata: { width: 100, height: 100, fps: 60, duration: 600, frames: 600, frameStride: 60, size: 123456 },
        annotationStatePerTask: [],
        annotationStatistics: {
            annotated: 0,
            partiallyAnnotated: 0,
            unannotated: 0,
        },
        uploadTime: '22 Jun 2022',
        uploaderId: 'user@intel.com',
        lastAnnotatorId: null,
        ...mediaItem,
    };
};

export const getMockedVideoFrameMediaItem = (mediaItem: Partial<VideoFrame>): VideoFrame => {
    return {
        identifier: { type: MEDIA_TYPE.VIDEO_FRAME, videoId: 'test-video', frameNumber: 0 },
        name: 'Test video',
        status: MEDIA_ANNOTATION_STATUS.NONE,
        src: '',
        thumbnailSrc: '',
        metadata: { width: 100, height: 100, fps: 60, duration: 600, frames: 600, frameStride: 60, size: 654321 },
        annotationStatePerTask: [],
        uploadTime: '22 Jun 2022',
        uploaderId: 'user@intel.com',
        lastAnnotatorId: null,
        ...mediaItem,
    };
};
