// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, View } from '@geti/ui';

import { useAnnotationFilters } from './use-annotation-filters.hook';
import { useHasStaleFilter } from './use-has-stale-filter.hook';

export const RefreshFilterButton = () => {
    const [filters, setFilters] = useAnnotationFilters();

    const resetFilter = () => {
        setFilters([...filters]);
    };

    const isStale = useHasStaleFilter();

    if (!isStale) {
        return <></>;
    }

    return (
        <View
            width={'100%'}
            backgroundColor='gray-50'
            borderWidth='thin'
            marginBottom='size-100'
            UNSAFE_style={{ borderColor: 'var(--energy-blue)' }}
        >
            <ActionButton
                isQuiet
                width={'100%'}
                UNSAFE_style={{ borderRadius: '0', textDecoration: 'underline', textAlign: 'left' }}
                id='label-filter-refresh'
                onPress={resetFilter}
            >
                Refresh filter
            </ActionButton>
        </View>
    );
};
