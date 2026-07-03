// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import { isEmpty } from 'lodash-es';

import { FilterPopoverButton } from '../../../../../../components/filter-popover-button/filter-popover-button.component';
import { MultiSelectList } from '../../../../../../components/multi-select-list/multi-select-list.component';
import { DatasetSubset } from '../../../../../../constants/shared-types';
import { pluralize } from '../../../../../../shared/util';

const SUBSET_OPTIONS: { id: DatasetSubset; name: string }[] = [
    { id: 'training', name: 'Training subset' },
    { id: 'validation', name: 'Validation subset' },
    { id: 'testing', name: 'Testing subset' },
    { id: 'unassigned', name: 'No subset' },
];

export const FilterBySubset = () => {
    const { selectedSubsets, setSelectedSubsets } = useDatasetFiltersSearchParams();

    const summary = isEmpty(selectedSubsets)
        ? null
        : `${selectedSubsets.length} ${pluralize(selectedSubsets.length, 'subset', 'subsets')} selected`;

    return (
        <FilterPopoverButton
            ariaLabel='Filter by subset'
            placeholder='Filter by subset'
            summary={summary}
            width='size-3000'
            dialogWidth='size-3000'
        >
            <MultiSelectList
                name='subsets'
                items={SUBSET_OPTIONS}
                selectAllLabel='All subsets'
                onSelectionChange={setSelectedSubsets}
                defaultSelectedKeys={new Set(selectedSubsets)}
            />
        </FilterPopoverButton>
    );
};
