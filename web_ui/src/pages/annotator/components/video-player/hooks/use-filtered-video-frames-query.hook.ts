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

import { useMemo } from 'react';

import { InfiniteData, UseInfiniteQueryResult } from '@tanstack/react-query';
import isEmpty from 'lodash/isEmpty';
import range from 'lodash/range';

import { AdvancedFilterOptions } from '../../../../../core/media/media-filter.interface';
import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideoFrame, VideoIdentifier } from '../../../../../core/media/video.interface';
import { useFilterSearchParam } from '../../../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import { useAdvancedFramesFilterQuery } from '../../../../media/hooks/media-items/advanced-frames-filter-query.hook';
import { useIsInActiveMode } from '../../../providers/dataset-provider/use-is-in-active-mode.hook';
import { useVideoPlayerContext } from '../video-player-provider.component';

const mediaItemsToLoad = 100;
export const useFilteredVideoFramesQuery = (
    selectedMediaItem: MediaItem | undefined
): { query: UseInfiniteQueryResult<InfiniteData<number[]>>; data: number[] } => {
    const isInActiveMode = useIsInActiveMode();
    const [mediaFilterOptions] = useFilterSearchParam<AdvancedFilterOptions>('filter', isInActiveMode);
    const videoPlayerCtx = useVideoPlayerContext();

    const enabled = selectedMediaItem !== undefined && isVideoFrame(selectedMediaItem);

    const query = useAdvancedFramesFilterQuery(
        (selectedMediaItem?.identifier as VideoIdentifier)?.videoId,
        {
            enabled: enabled && !isEmpty(mediaFilterOptions),
            // @ts-expect-error The useAdvancedFramesFilterQuery hook does allow us to overwrite the
            // expected data type when using select, so let's ignore the error
            select: (data) => {
                const [page] = data?.pages ?? [{ videoFrames: [], totalMatchedVideoFrames: 0, nextPage: undefined }];
                const filteredFramesSet = new Set(
                    page.videoFrames.map(({ identifier: { frameNumber } }) => frameNumber)
                );

                const videoFrames = enabled ? range(0, selectedMediaItem.metadata.frames, videoPlayerCtx?.step) : [];
                const filteredFrames = videoFrames?.filter((frameNumber) => filteredFramesSet.has(frameNumber));
                return { pages: [filteredFrames], pageParams: data.pageParams };
            },
        },
        mediaItemsToLoad,
        mediaFilterOptions,
        {}
    ) as unknown as UseInfiniteQueryResult<InfiniteData<number[]>>;

    const frameNumbers = useMemo(() => {
        return query.data?.pages.flatMap((data) => data) ?? [];
    }, [query.data]);

    return { query, data: frameNumbers };
};
