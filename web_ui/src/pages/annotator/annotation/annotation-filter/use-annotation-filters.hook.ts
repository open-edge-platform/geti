// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useMemo } from 'react';

import { v4 as uuidV4 } from 'uuid';

import {
    AdvancedFilterOptions,
    SearchRuleField,
    SearchRuleOperator,
} from '../../../../core/media/media-filter.interface';
import { useFilterSearchParam } from '../../../../hooks/use-filter-search-param/use-filter-search-param.hook';

type UseAnnotationFilters = [string[], (f: string[]) => void];

// Annotation filters are stored in the browser's URL, this makes it easy to access them
// without having to add another provider and also makes the state shareable.
// One "hidden" implementation detail with these is that the useOutputAnnotationsFilter
// hook is refreshed whenever the filters are changed.
// The RefreshFilterButton component uses this to refresh annotations by calling setFilters(filters),
// which generates new ids for the filter and thus refrehses annotations
export const useAnnotationFilters = (): UseAnnotationFilters => {
    const [filterOptions, setFilterOptions] = useFilterSearchParam<AdvancedFilterOptions>('annotations-filter');

    const filters = useMemo(() => {
        const rules = filterOptions?.rules ?? [];
        const labels = rules.filter(({ field }) => field === SearchRuleField.LabelId).flatMap(({ value }) => value);

        return (labels ?? []) as string[];
    }, [filterOptions.rules]);

    const setFilters = useCallback(
        (newFilters: string[]) => {
            setFilterOptions({
                condition: 'and',
                rules: [
                    {
                        field: SearchRuleField.LabelId,
                        id: uuidV4(),
                        operator: SearchRuleOperator.In,
                        value: newFilters,
                    },
                ],
            });
        },
        [setFilterOptions]
    );

    return [filters, setFilters];
};
