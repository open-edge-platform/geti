// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import dayjs from 'dayjs';
import isEqual from 'lodash/isEqual';

import { isImage } from '../../../../../core/media/image.interface';
import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideo, isVideoFrame, VideoFrame } from '../../../../../core/media/video.interface';

export const isSelected = (
    mediaItem: MediaItem,
    selectedMediaItem: MediaItem | undefined,
    framesDisplayedSeparately = false
): boolean => {
    if (selectedMediaItem === undefined) {
        return false;
    }

    if (isImage(selectedMediaItem)) {
        if (isImage(mediaItem)) {
            return selectedMediaItem.identifier.imageId === mediaItem.identifier.imageId;
        }
    } else {
        if (isVideo(mediaItem) || isVideoFrame(mediaItem)) {
            const isSameVideo = selectedMediaItem.identifier.videoId === mediaItem.identifier.videoId;

            if (framesDisplayedSeparately && isVideoFrame(mediaItem) && isSameVideo) {
                return (selectedMediaItem as VideoFrame).identifier.frameNumber === mediaItem.identifier.frameNumber;
            }

            return isSameVideo;
        }
    }

    return isEqual(selectedMediaItem.identifier, mediaItem.identifier);
};

export const formatUploadTime = (date: string): string => dayjs(date).format('DD.MM.YY');
