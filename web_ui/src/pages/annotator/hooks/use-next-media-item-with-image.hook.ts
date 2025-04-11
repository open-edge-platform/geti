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

import { findNextCriteria, findNextVideoFrameCriteria } from '../components/utils';
import { useConstructVideoFrame } from '../components/video-player/hooks/use-construct-video-frame.hook';
import { useSelectedMediaItem } from '../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useLoadImageQuery } from '../providers/selected-media-item-provider/use-load-image-query.hook';
import { useNextMediaItem } from './use-next-media-item.hook';

export const useNextMediaItemWithImage = () => {
    const { selectedMediaItem } = useSelectedMediaItem();

    const nextMediaItemCriteria = useNextMediaItem(
        selectedMediaItem,
        findNextCriteria,
        findNextVideoFrameCriteria,
        () => undefined
    );
    const constructVideoFrame = useConstructVideoFrame(selectedMediaItem);
    const nextMediaItem =
        nextMediaItemCriteria?.type === 'media'
            ? nextMediaItemCriteria.media
            : nextMediaItemCriteria?.type === 'videoFrame'
              ? constructVideoFrame(nextMediaItemCriteria.frameNumber)
              : undefined;

    const imageQuery = useLoadImageQuery(nextMediaItem);

    if (nextMediaItem === undefined || imageQuery.data === undefined) {
        return undefined;
    }

    return {
        ...nextMediaItem,
        image: imageQuery.data,
    };
};
