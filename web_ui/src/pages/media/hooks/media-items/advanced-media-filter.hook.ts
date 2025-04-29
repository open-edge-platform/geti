// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useRef } from 'react';

import { InfiniteData } from '@tanstack/react-query';

import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../../../core/media/media-filter.interface';
import { MediaAdvancedCount, MediaAdvancedFilterResponse, MediaItem } from '../../../../core/media/media.interface';
import { MediaService } from '../../../../core/media/services/media-service.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { useAdvancedFilterQuery, type UseAdvancedFilterQueryOptions } from './advanced-filter-query.hook';

interface UseAdvancedMediaFilterProps {
    mediaService: MediaService;
    mediaItemsLoadSize: number;
    datasetIdentifier: DatasetIdentifier;
    mediaFilterOptions: AdvancedFilterOptions;
    queryOptions: UseAdvancedFilterQueryOptions;
    sortingOptions: AdvancedFilterSortingOptions;
    onSuccess?: (data: InfiniteData<MediaAdvancedFilterResponse>) => void;
}

interface UseAdvancedMediaFilter extends MediaAdvancedCount {
    media: MediaItem[];
    isLoading: boolean;
    isMediaFetching: boolean;
    loadNextMedia: (init?: boolean) => Promise<void>;
    isFetchingNextPage: boolean;
}

export const useAdvancedMediaFilter = ({
    mediaService,
    datasetIdentifier,
    queryOptions = {},
    mediaItemsLoadSize,
    mediaFilterOptions,
    sortingOptions,
    onSuccess,
}: UseAdvancedMediaFilterProps): UseAdvancedMediaFilter => {
    const handleSuccessRef = useRef(onSuccess);

    const mediaQuery = useAdvancedFilterQuery(
        mediaService,
        datasetIdentifier,
        {
            ...queryOptions,
            retry: false,
            meta: { notifyOnError: true },
        },
        mediaItemsLoadSize,
        mediaFilterOptions,
        sortingOptions
    );

    const { isFetching, isFetchingNextPage, isFetchingPreviousPage, refetch, hasNextPage, fetchNextPage } = mediaQuery;

    const media = mediaQuery.data?.pages?.flatMap((response: MediaAdvancedFilterResponse) => response.media) ?? [];

    const {
        totalImages = 0,
        totalVideos = 0,
        totalMatchedImages = 0,
        totalMatchedVideos = 0,
        totalMatchedVideoFrames = 0,
    } = mediaQuery.data?.pages[0] ?? {};

    const isMediaFetching = isFetching || isFetchingNextPage || isFetchingPreviousPage;

    const loadNextMedia = useCallback(
        async (init = false) => {
            if (init) {
                await refetch();
            } else if (!isFetching && hasNextPage) {
                await fetchNextPage();
            }
        },
        [isFetching, hasNextPage, refetch, fetchNextPage]
    );

    useEffect(() => {
        handleSuccessRef.current = onSuccess;
    }, [onSuccess]);

    useEffect(() => {
        if (!queryOptions.enabled || !mediaQuery.isSuccess || handleSuccessRef.current === undefined) {
            return;
        }

        handleSuccessRef.current(mediaQuery.data);
    }, [queryOptions.enabled, mediaQuery.isSuccess, mediaQuery.data]);

    return {
        media,
        totalImages,
        totalMatchedImages,
        totalMatchedVideoFrames,
        totalMatchedVideos,
        totalVideos,
        isMediaFetching,
        loadNextMedia,
        isFetchingNextPage,
        isLoading: mediaQuery.isPending,
    };
};
