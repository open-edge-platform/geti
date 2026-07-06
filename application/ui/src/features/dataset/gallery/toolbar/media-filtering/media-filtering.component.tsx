// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex } from '@geti-ui/ui';

import { FilterByStatus } from './filter-by-status/filter-by-status.component';
import { MediaFilterLabels } from './media-filter-labels/media-filter-labels.component';
import { MoreMediaFilters } from './more-media-filters.component';

export const MediaFiltering = () => {
    return (
        <Flex direction={'row'} gap={'size-200'} alignItems={'center'}>
            <FilterByStatus width={'size-3000'} />
            <MediaFilterLabels />
            <MoreMediaFilters />
        </Flex>
    );
};
