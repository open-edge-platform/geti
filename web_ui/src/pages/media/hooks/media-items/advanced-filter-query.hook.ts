// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    InfiniteData,
    QueryKey,
    useInfiniteQuery,
    UseInfiniteQueryOptions,
    UseInfiniteQueryResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../../../core/media/media-filter.interface';
import { MediaAdvancedFilterResponse } from '../../../../core/media/media.interface';
import { MediaService } from '../../../../core/media/services/media-service.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { NextPageURL } from '../../../../core/shared/infinite-query.interface';

export type UseAdvancedFilterQueryOptions = Pick<
    UseInfiniteQueryOptions<
        MediaAdvancedFilterResponse,
        AxiosError,
        MediaAdvancedFilterResponse,
        MediaAdvancedFilterResponse,
        QueryKey,
        NextPageURL
    >,
    'retry' | 'meta' | 'enabled'
>;

export const useAdvancedFilterQuery = (
    mediaService: MediaService,
    datasetIdentifier: DatasetIdentifier,
    queryOptions: UseAdvancedFilterQueryOptions = {},
    mediaItemsLoadSize = 50,
    searchOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions
): UseInfiniteQueryResult<InfiniteData<MediaAdvancedFilterResponse>, AxiosError> => {
    const mediaQueryKey = QUERY_KEYS.ADVANCED_MEDIA_ITEMS(datasetIdentifier, searchOptions, sortingOptions);

    return useInfiniteQuery<
        MediaAdvancedFilterResponse,
        AxiosError,
        InfiniteData<MediaAdvancedFilterResponse>,
        QueryKey,
        NextPageURL
    >({
        queryKey: mediaQueryKey,
        queryFn: async ({ pageParam: nextPage = null }) => {
            return mediaService.getAdvancedFilterMedia(
                datasetIdentifier,
                mediaItemsLoadSize,
                nextPage,
                searchOptions,
                sortingOptions
            );
        },
        getPreviousPageParam: () => undefined,
        getNextPageParam: ({ nextPage }) => nextPage,
        initialPageParam: null,
        ...queryOptions,
    });
};
