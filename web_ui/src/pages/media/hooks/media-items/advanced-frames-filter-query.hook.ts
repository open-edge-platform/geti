// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
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
