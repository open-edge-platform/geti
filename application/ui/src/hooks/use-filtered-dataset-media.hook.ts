// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useDatasetMediaFilterOptions } from './use-dataset-media-filter-options.hook';
import { useGetDatasetMediaItems } from './use-get-dataset-media-items.hook';

/**
 * Lists the media of the dataset (or of the selected dataset view), with the filters and sorting from the URL.
 */
export const useFilteredDatasetMedia = () => {
    const { fetchNextPage, hasNextPage, isFetchingNextPage, ...rest } =
        useGetDatasetMediaItems(useDatasetMediaFilterOptions());

    return {
        ...rest,
        hasNextPage,
        isFetchingNextPage,
        fetchNextPage: () => {
            if (hasNextPage && !isFetchingNextPage) {
                void fetchNextPage();
            }
        },
    };
};
