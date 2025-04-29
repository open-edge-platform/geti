// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
