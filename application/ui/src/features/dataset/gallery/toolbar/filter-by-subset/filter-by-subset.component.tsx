// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Content, Dialog, DialogTrigger, Flex, PressableElement, Text } from '@geti-ui/ui';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import { isEmpty } from 'lodash-es';

import { MultiSelectList } from '../../../../../components/multi-select-list/multi-select-list.component';
import { DatasetSubset } from '../../../../../constants/shared-types';
import { FilterChips } from '../filter-chips/filter-chips.component';

import classes from './filter-by-subset.module.scss';

const SUBSET_OPTIONS: { id: DatasetSubset; name: string }[] = [
    { id: 'training', name: 'Training' },
    { id: 'validation', name: 'Validation' },
    { id: 'testing', name: 'Testing' },
    { id: 'unassigned', name: 'Unassigned' },
];

export const FilterBySubset = () => {
    const { selectedSubsets, setSelectedSubsets } = useDatasetFiltersSearchParams();

    const handleSelectionChange = (selectedKeys: Set<string> | 'all') => {
        const subsets =
            selectedKeys === 'all'
                ? SUBSET_OPTIONS.map(({ id }) => id)
                : (Array.from(selectedKeys) as DatasetSubset[]);

        setSelectedSubsets(subsets);
    };

    const handleRemoveFilter = (subset: DatasetSubset) => {
        setSelectedSubsets(selectedSubsets.filter((selectedSubset) => selectedSubset !== subset));
    };

    const selectedOptions = SUBSET_OPTIONS.filter(({ id }) => selectedSubsets.includes(id));

    return (
        <DialogTrigger hideArrow type='popover'>
            <PressableElement>
                <div role='button' aria-label='Filter by subset'>
                    <Flex
                        gap={'size-40'}
                        wrap={'wrap'}
                        width={'size-3000'}
                        height={'size-400'}
                        alignItems={'center'}
                        UNSAFE_className={classes.filterContainer}
                    >
                        {selectedOptions.map((option) => (
                            <FilterChips
                                key={option.id}
                                name={option.name}
                                onClose={() => handleRemoveFilter(option.id)}
                            />
                        ))}

                        {isEmpty(selectedOptions) && (
                            <Text UNSAFE_className={classes.searchPlaceholder}>All subsets</Text>
                        )}
                    </Flex>
                </div>
            </PressableElement>

            <Dialog width={'size-3000'} UNSAFE_className={classes.dialog} aria-label='Filter media items'>
                <Content>
                    <MultiSelectList
                        name='subsets'
                        items={SUBSET_OPTIONS}
                        selectAllLabel='Toggle all'
                        onSelectionChange={handleSelectionChange}
                        defaultSelectedKeys={new Set(selectedSubsets)}
                    />
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};

