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
