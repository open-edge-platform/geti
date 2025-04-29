// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
