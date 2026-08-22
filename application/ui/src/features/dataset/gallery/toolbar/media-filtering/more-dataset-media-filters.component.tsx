// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
    ActionButton,
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    Tooltip,
    TooltipTrigger,
} from '@geti-ui/ui';
import { Filter } from '@geti-ui/ui/icons';
import { useTranslation } from 'react-i18next';

import { DateFilter } from './date-filter/date-filter.component';
import { FilterBySubset } from './filter-by-subset/filter-by-subset.component';

export const MoreDatasetMediaFilters = () => {
    const { t } = useTranslation();

    return (
        <DialogTrigger type={'popover'} placement={'bottom'}>
            <TooltipTrigger>
                <ActionButton isQuiet aria-label={t('dataset.moreFilters')}>
                    <Filter />
                </ActionButton>
                <Tooltip>{t('dataset.moreFilters')}</Tooltip>
            </TooltipTrigger>
            <Dialog size='S'>
                <Heading>{t('dataset.moreFilters')}</Heading>
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
