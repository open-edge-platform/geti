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
