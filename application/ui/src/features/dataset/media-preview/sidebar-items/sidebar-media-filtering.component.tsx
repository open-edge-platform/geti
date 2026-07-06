// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Divider, Flex } from '@geti-ui/ui';

import {
    ActiveFiltersList,
    useClearAllFilters,
    useHasActiveFilters,
} from '../../gallery/active-filters/active-filters.component';
import { AnnotatorMediaFilteringCompact } from '../../gallery/toolbar/media-filtering/annotator-media-filtering-compact.component';

export const SidebarMediaFilter = () => {
    const hasActiveFilters = useHasActiveFilters();
    const handleClearAll = useClearAllFilters();

    return (
        <Flex direction={'column'} gap={'size-100'}>
            <Flex justifyContent={'space-between'} alignItems={'center'}>
                <AnnotatorMediaFilteringCompact />
                {hasActiveFilters && (
                    <ActionButton isQuiet onPress={handleClearAll}>
                        Clear all
                    </ActionButton>
                )}
            </Flex>
            <Divider size='S' orientation='horizontal' />
            {hasActiveFilters && (
                <Flex gap='size-100' wrap>
                    <ActiveFiltersList />
                </Flex>
            )}
        </Flex>
    );
};
