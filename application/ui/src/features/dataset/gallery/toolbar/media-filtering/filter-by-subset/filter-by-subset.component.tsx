// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { DatasetSubset } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Checkbox, CheckboxGroup, Flex, Text } from '@geti-ui/ui';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';

import { SUBSET_LABEL_KEYS, SUBSETS } from '../../../../../../shared/subsets';

import classes from './filter-by-subset.module.scss';

export const FilterBySubset = () => {
    const { t } = useTranslation();
    const { selectedSubsets, setSelectedSubsets } = useDatasetFiltersSearchParams();

    const handleSelectionChange = (values: string[]) => {
        setSelectedSubsets(values as DatasetSubset[]);
    };

    return (
        <Flex direction='column' gap='size-100'>
            <Text UNSAFE_className={classes.label}>{t('dataset.filters.subset')}</Text>
            <Flex direction='column'>
                <CheckboxGroup value={selectedSubsets} onChange={handleSelectionChange}>
                    <>
                        {SUBSETS.map((subset) => (
                            <Checkbox key={subset} value={subset}>
                                {t(SUBSET_LABEL_KEYS[subset])}
                            </Checkbox>
                        ))}
                    </>
                </CheckboxGroup>
            </Flex>
        </Flex>
    );
};
