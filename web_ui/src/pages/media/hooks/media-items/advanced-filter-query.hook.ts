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
