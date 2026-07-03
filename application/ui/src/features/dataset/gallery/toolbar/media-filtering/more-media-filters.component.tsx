// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Content, Dialog, DialogTrigger, Divider, Flex, Heading } from '@geti-ui/ui';
import { Filter } from '@geti-ui/ui/icons';

import { DateFilter } from './date-filter/date-filter.component';
import { FilterBySubset } from './filter-by-subset/filter-by-subset.component';

export const MoreMediaFilters = () => {
    return (
        <DialogTrigger type={'popover'} placement={'bottom'}>
            <ActionButton isQuiet aria-label={'More filters'}>
                <Filter />
            </ActionButton>
            <Dialog size='S'>
                <Heading>More filters</Heading>
                <Divider />
                <Content>
                    <Flex direction='column' gap='size-300'>
                        <DateFilter />

                        <Divider size='M' />

                        <FilterBySubset />
                    </Flex>
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
