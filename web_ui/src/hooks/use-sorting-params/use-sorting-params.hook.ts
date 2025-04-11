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

import { useSearchParams } from 'react-router-dom';

import { AdvancedFilterSortingOptions, SortMenuActionKey } from '../../core/media/media-filter.interface';

export const useSortingParams = () => {
    const [searchParams, setSearchParams] = useSearchParams();

    const setSortingOptions = ({ sortBy, sortDir }: { sortBy?: string; sortDir?: string }) => {
        sortBy && searchParams.set('sortBy', sortBy);
        sortDir && searchParams.set('sortDirection', sortDir);
        setSearchParams(searchParams);
    };

    const sortingOptions: AdvancedFilterSortingOptions = {
        sortBy: searchParams.get('sortBy') ?? SortMenuActionKey.DATE,
        sortDir: searchParams.get('sortDirection') ?? 'dsc',
    };

    return {
        setSortingOptions,
        sortingOptions,
    };
};
