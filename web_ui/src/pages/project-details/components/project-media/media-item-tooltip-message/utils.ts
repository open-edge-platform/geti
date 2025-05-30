// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isImage } from '../../../../../core/media/image.interface';
import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideo, isVideoFrame } from '../../../../../core/media/video.interface';
import { getFileSize } from '../../../../../shared/utils';
import { MediaItemTooltipMessageProps } from './media-item-tooltip-message';

export const DELETE_ANOMALY_VIDEO_WARNING = 'Selected frames will be deleted from both anomaly and normal bucket.';

export const getMediaItemTooltipProps = (mediaItem: MediaItem): MediaItemTooltipMessageProps => {
    if (isImage(mediaItem)) {
        const {
            name,
            uploadTime,
            uploaderId,
            metadata: { height, width, size },
            identifier: { imageId, type },
            lastAnnotatorId,
        } = mediaItem;

        return {
            type,
            uploadTime,
            uploaderId,
            id: imageId,
            fileName: name,
            fileSize: getFileSize(size),
            resolution: `${width}x${height}`,
            lastAnnotatorId,
        };
    } else if (isVideo(mediaItem) || isVideoFrame(mediaItem)) {
        const {
            name,
            uploadTime,
            uploaderId,
            identifier: { type, videoId },
            metadata: { fps, duration, size, width, height },
            lastAnnotatorId,
        } = mediaItem;

        return {
            type,
            fps,
            duration,
            uploadTime,
            uploaderId,
            id: videoId,
            fileName: name,
            resolution: `${width}x${height}`,
            fileSize: getFileSize(size),
            lastAnnotatorId,
        };
    }

    throw new Error('Unable to retrieve media type information');
};
