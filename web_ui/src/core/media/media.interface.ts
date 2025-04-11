// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

/* DO NOT REMOVE TYPE KEYWORD FROM IMPORTS BELOW, it's needed for playwright to be happy */

import type {
    MEDIA_CONTENT_BUCKET,
    QueuedListItem,
} from '../../providers/media-upload-provider/media-upload.interface';
import type { DatasetIdentifier } from '../projects/dataset.interface';
import { NextPageURL } from '../shared/infinite-query.interface';
import { MEDIA_TYPE } from './base-media.interface';
import { Image } from './image.interface';
import { FilterVideoFrame, Video, VideoFrame } from './video.interface';

export type MediaItem = Image | Video | VideoFrame;
export type MediaIdentifier = MediaItem['identifier'];
export type MediaCount = { images: number; videos: number };

export interface UploadProgress {
    uploadId: string;
    datasetIdentifier: DatasetIdentifier;
    file: File;
    fileSize: number;
    fileName: string;
    fileType: string;
    progress: number;
    meta?: MEDIA_CONTENT_BUCKET;
}

export interface MediaItemResponse {
    media: MediaItem[];
    nextPage: NextPageURL;
    mediaCount: MediaCount | undefined;
}

export interface MediaAdvancedCount {
    totalImages: number;
    totalMatchedImages: number;
    totalMatchedVideoFrames: number;
    totalMatchedVideos: number;
    totalVideos: number;
}

export interface MediaAdvancedFilterResponse extends MediaAdvancedCount {
    media: MediaItem[];
    nextPage: NextPageURL;
}

export interface MediaAdvancedFramesFilterResponse {
    nextPage: NextPageURL;
    videoFrames: FilterVideoFrame[];
    totalMatchedVideoFrames: number;
}

export type MediaItemsQueryResponse = MediaItemResponse | MediaAdvancedFilterResponse;

export interface UploadMediaProps {
    datasetIdentifier: DatasetIdentifier;
    uploadId: string;
    media: QueuedListItem;
    onProgress: (uploadProgressProps: UploadProgress) => void;
    abortController: AbortController;
}

export interface UploadMediaMutationResponse {
    datasetIdentifier: DatasetIdentifier;
    uploadId: string;
    media: QueuedListItem;
    abortController: AbortController;
}

export const mediaIdentifierToString = (mediaIdentifier: MediaIdentifier): string => {
    switch (mediaIdentifier.type) {
        case MEDIA_TYPE.IMAGE:
            return `image-${mediaIdentifier.imageId}`;
        case MEDIA_TYPE.VIDEO:
            return `video-${mediaIdentifier.videoId}`;
        case MEDIA_TYPE.VIDEO_FRAME:
            return `videoframe-${mediaIdentifier.videoId}-${mediaIdentifier.frameNumber}`;
    }
};
