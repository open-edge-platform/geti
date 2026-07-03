// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex } from '@geti-ui/ui';

import { DateFilter } from './date-filter/date-filter.component';
import { FilterByStatus } from './filter-by-status/filter-by-status.component';
import { FilterBySubset } from './filter-by-subset/filter-by-subset.component';
import { MediaFilterLabels } from './media-filter-labels/media-filter-labels.component';

export const MediaFiltering = () => {
    return (
        <Flex direction={'row'} gap={'size-200'} alignItems={'center'}>
            <FilterByStatus />
            <MediaFilterLabels />
            <FilterBySubset />
            <DateFilter />
        </Flex>
    );
};
