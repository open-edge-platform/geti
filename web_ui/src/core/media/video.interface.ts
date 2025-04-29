// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MEDIA_TYPE } from './base-media.interface';
import { BaseIdentifier, BaseMediaItem, BaseMetadata } from './base.interface';

export interface VideoIdentifier extends BaseIdentifier {
    type: MEDIA_TYPE.VIDEO;
    videoId: string;
}

export interface VideoMetadata extends BaseMetadata {
    fps: number;
    frames: number;
    duration: number;
    frameStride: number;
}

export interface VideoStatistics {
    annotated: number;
    partiallyAnnotated: number;
    unannotated: number;
}

export interface Video extends BaseMediaItem {
    identifier: VideoIdentifier;
    metadata: VideoMetadata;
    matchedFrames?: number;
    annotationStatistics?: VideoStatistics;
}

export const isVideo = (media: { identifier: BaseIdentifier } | undefined): media is Video => {
    return media !== undefined && media.identifier.type === MEDIA_TYPE.VIDEO;
};

export interface VideoFrameIdentifier extends BaseIdentifier {
    type: MEDIA_TYPE.VIDEO_FRAME;
    videoId: string;
    frameNumber: number;
}
export interface VideoFrame extends BaseMediaItem {
    identifier: VideoFrameIdentifier;
    metadata: VideoMetadata;
}

export type FilterVideoFrame = Omit<VideoFrame, 'metadata' | 'lastAnnotatorId'> & {
    metadata: {
        height: number;
        width: number;
    };
};

export const isVideoFrame = (media: { identifier: BaseIdentifier } | undefined): media is VideoFrame => {
    return media !== undefined && media.identifier.type === MEDIA_TYPE.VIDEO_FRAME;
};
