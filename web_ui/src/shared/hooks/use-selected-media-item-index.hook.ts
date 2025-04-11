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

import isEqual from 'lodash/isEqual';

import { MEDIA_TYPE } from '../../core/media/base-media.interface';
import { MediaIdentifier, MediaItem } from '../../core/media/media.interface';
import { isVideoFrame } from '../../core/media/video.interface';
import { TestMediaItem } from '../../core/tests/test-media.interface';

const getMediaItemIdentifierId = (
    media: MediaItem | undefined,
    isInActiveMode: boolean,
    framesShownSeparately?: boolean
): null | MediaIdentifier => {
    if (media === undefined) {
        return null;
    }

    // In the active set we show video frames separately, so we want to scroll to them
    if (isInActiveMode) {
        return media.identifier;
    }

    // In the dataset we want video frames to scroll to the associated video in the dataset list
    if (isVideoFrame(media) && !framesShownSeparately) {
        return { type: MEDIA_TYPE.VIDEO, videoId: media.identifier.videoId };
    }

    return media.identifier;
};

export const useSelectedMediaItemIndex = (
    mediaItems: MediaItem[] | TestMediaItem[],
    selectedMediaItem: MediaItem | undefined,
    isInActiveMode: boolean,
    framesShownSeparately?: boolean
): number => {
    return useMemo(() => {
        const selectedIdentifier = getMediaItemIdentifierId(selectedMediaItem, isInActiveMode, framesShownSeparately);

        return mediaItems.findIndex((item) =>
            isEqual(
                getMediaItemIdentifierId('media' in item ? item.media : item, isInActiveMode, framesShownSeparately),
                selectedIdentifier
            )
        );
    }, [mediaItems, selectedMediaItem, isInActiveMode, framesShownSeparately]);
};
