// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
        sortDir: searchParams.get('sortDirection') === 'asc' ? 'asc' : 'dsc',
    };

    return {
        setSortingOptions,
        sortingOptions,
    };
};
