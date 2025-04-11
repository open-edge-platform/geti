// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { View } from '@adobe/react-spectrum';

import { ActionButton } from '../../../../shared/components/button/button.component';
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
