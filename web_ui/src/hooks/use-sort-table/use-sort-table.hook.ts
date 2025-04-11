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

import { Dispatch, SetStateAction, useState } from 'react';

import { SortingOptions, SortingParams } from '../../shared/components/table/table.interface';

interface UseSortTable<T extends Partial<SortingOptions>> {
    queryOptions: T;
    setQueryOptions: Dispatch<SetStateAction<T>>;
}

export const useSortTable = <T extends Partial<SortingOptions>>({ queryOptions, setQueryOptions }: UseSortTable<T>) => {
    const [sortingOptions, setSortingOptions] = useState<SortingOptions>({
        sortBy: queryOptions.sortBy,
        sortDirection: queryOptions.sortDirection,
    });

    const sort: SortingParams['sort'] = ({ sortBy }) => {
        const newSortingOptions: SortingOptions = { ...sortingOptions };
        const newQueryOptions: T = { ...queryOptions };

        newSortingOptions.sortBy = sortBy;
        newQueryOptions.sortBy = sortBy as string;

        if (
            // initial sorting or sorting by the same column
            sortingOptions.sortBy === sortBy ||
            sortingOptions.sortBy === undefined
        ) {
            if (sortingOptions.sortDirection === 'ASC') {
                newSortingOptions.sortDirection = 'DESC';
                newQueryOptions.sortDirection = 'DESC';
            } else {
                newSortingOptions.sortDirection = 'ASC';
                newQueryOptions.sortDirection = 'ASC';
            }
        } else {
            // sorting by different column

            newSortingOptions.sortDirection = sortingOptions.sortDirection;
            newQueryOptions.sortDirection = sortingOptions.sortDirection;
        }

        setQueryOptions(newQueryOptions);
        setSortingOptions(newSortingOptions);
    };

    return [sortingOptions, sort] as const;
};
