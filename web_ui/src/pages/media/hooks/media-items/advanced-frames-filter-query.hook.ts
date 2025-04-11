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

import {
    InfiniteData,
    QueryKey,
    useInfiniteQuery,
    UseInfiniteQueryOptions,
    UseInfiniteQueryResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../../../core/media/media-filter.interface';
import { MediaAdvancedFramesFilterResponse } from '../../../../core/media/media.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';
import { NextPageURL } from '../../../../core/shared/infinite-query.interface';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';

export const useAdvancedFramesFilterQuery = (
    videoId: string,
    queryOptions: Pick<
        UseInfiniteQueryOptions<
            MediaAdvancedFramesFilterResponse,
            AxiosError,
            MediaAdvancedFramesFilterResponse,
            MediaAdvancedFramesFilterResponse,
            QueryKey,
            NextPageURL
        >,
        'enabled' | 'select'
    > = {},
    mediaItemsLoadSize = 50,
    searchOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions
): UseInfiniteQueryResult<InfiniteData<MediaAdvancedFramesFilterResponse>, AxiosError> => {
    const { mediaService } = useApplicationServices();
    const datasetIdentifier = useDatasetIdentifier();
    const mediaQueryKey = QUERY_KEYS.ADVANCED_MEDIA_FRAME_ITEMS(datasetIdentifier, searchOptions, sortingOptions);

    return useInfiniteQuery<
        MediaAdvancedFramesFilterResponse,
        AxiosError,
        InfiniteData<MediaAdvancedFramesFilterResponse>,
        QueryKey,
        NextPageURL
    >(
        // @ts-expect-error There is an issue with type for "select" function.
        {
            queryKey: mediaQueryKey,
            queryFn: ({ pageParam: nextPage = null }) =>
                mediaService.getAdvancedFramesFilter({
                    videoId,
                    nextPage,
                    searchOptions,
                    sortingOptions,
                    datasetIdentifier,
                    mediaItemsLoadSize,
                }),
            getPreviousPageParam: () => undefined,
            getNextPageParam: ({ nextPage }) => nextPage,
            initialPageParam: undefined,
            ...queryOptions,
        }
    );
};
