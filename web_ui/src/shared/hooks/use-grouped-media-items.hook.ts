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

import { useMemo } from 'react';

import groupBy from 'lodash/groupBy';
import isEmpty from 'lodash/isEmpty';

import { MediaItem } from '../../core/media/media.interface';
import { isVideo, isVideoFrame } from '../../core/media/video.interface';
import { TestMediaItem } from '../../core/tests/test-media.interface';

export const useGroupedMediaItems = (mediaItems: (MediaItem | TestMediaItem)[]) => {
    return useMemo<MediaItem[]>(() => {
        const mediaItemsByGroup = groupBy(mediaItems, (mediaItem) => {
            const item = 'media' in mediaItem ? mediaItem.media : mediaItem;
            if (isVideoFrame(item) || isVideo(item)) {
                return item.identifier.videoId;
            }

            return item.identifier.imageId;
        });

        // Return only 1 media item per group (i.e. one frame per video)
        const groupedMediaItems = Object.values(mediaItemsByGroup)
            .flatMap((items) => (!isEmpty(items) ? items[0] : undefined))
            .filter((mediaItem): mediaItem is MediaItem => mediaItem !== undefined);

        return groupedMediaItems;
    }, [mediaItems]);
};
