// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { Checkbox, CheckboxGroup, Flex, Text } from '@geti-ui/ui';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

import { DatasetSubset } from '../../../../../../constants/shared-types';

import classes from './filter-by-subset.module.scss';

const SUBSET_OPTIONS: { id: DatasetSubset; name: string }[] = [
    { id: 'training', name: 'Training subset' },
    { id: 'validation', name: 'Validation subset' },
    { id: 'testing', name: 'Testing subset' },
    { id: 'unassigned', name: 'No subset' },
];

export const FilterBySubset = () => {
    const { selectedSubsets, setSelectedSubsets } = useDatasetFiltersSearchParams();

    const [selectedSubsetsKeys, setSelectedSubsetsKeys] = useState<string[]>(selectedSubsets);

    const handleSelectionChange = (values: string[]) => {
        setSelectedSubsetsKeys(values);
        setSelectedSubsets(values as DatasetSubset[]);
    };

    const handleSelectAll = (isSelected: boolean) => {
        if (isSelected) {
            setSelectedSubsets(SUBSET_OPTIONS.map((option) => option.id));
            setSelectedSubsetsKeys(SUBSET_OPTIONS.map((option) => option.id));
            return;
        }

        setSelectedSubsets([]);
        setSelectedSubsetsKeys([]);
    };

    return (
        <Flex direction='column' gap='size-100'>
            <Text UNSAFE_className={classes.label}>Filter by subset</Text>
            <Flex direction='column'>
                <Checkbox
                    value='all'
                    isSelected={selectedSubsetsKeys.length === SUBSET_OPTIONS.length}
                    onChange={handleSelectAll}
                >
                    All subsets
                </Checkbox>
                <CheckboxGroup value={selectedSubsetsKeys} onChange={handleSelectionChange}>
                    <>
                        {SUBSET_OPTIONS.map((item) => (
                            <Checkbox key={item.id} value={item.id}>
                                {item.name}
                            </Checkbox>
                        ))}
                    </>
                </CheckboxGroup>
            </Flex>
        </Flex>
    );
};
