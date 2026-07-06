// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { Checkbox, CheckboxGroup, Flex, Text } from '@geti-ui/ui';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import capitalize from 'lodash-es/capitalize';

import { DatasetSubset } from '../../../../../../constants/shared-types';

import classes from './filter-by-subset.module.scss';

const SUBSET_OPTIONS: { name: DatasetSubset }[] = [
    { name: 'training' },
    { name: 'validation' },
    { name: 'testing' },
    { name: 'unassigned' },
];

export const FilterBySubset = () => {
    const { selectedSubsets, setSelectedSubsets } = useDatasetFiltersSearchParams();

    const [selectedSubsetsKeys, setSelectedSubsetsKeys] = useState<string[]>(selectedSubsets);

    const handleSelectionChange = (values: string[]) => {
        setSelectedSubsetsKeys(values);
        setSelectedSubsets(values as DatasetSubset[]);
    };

    return (
        <Flex direction='column' gap='size-100'>
            <Text UNSAFE_className={classes.label}>Filter by subset</Text>
            <Flex direction='column'>
                <CheckboxGroup value={selectedSubsetsKeys} onChange={handleSelectionChange}>
                    <>
                        {SUBSET_OPTIONS.map((item) => (
                            <Checkbox key={item.name} value={item.name}>
                                {capitalize(item.name)}
                            </Checkbox>
                        ))}
                    </>
                </CheckboxGroup>
            </Flex>
        </Flex>
    );
};
