// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Text } from '@adobe/react-spectrum';

interface EntitiesCounterProps {
    totalMatchedCount: number;
    totalCount: number;
    hasFilters: boolean;
    entity: string;
}

export const EntitiesCounter: FC<EntitiesCounterProps> = ({
    totalMatchedCount,
    totalCount,
    hasFilters,
    entity,
}): JSX.Element => {
    const text = `${entity}${totalMatchedCount === 1 ? '' : 's'}`;

    if (hasFilters && totalCount > 0) {
        return (
            <Text id={`${entity}-count-text`}>
                {totalMatchedCount} out of {totalCount} {text}
            </Text>
        );
    }

    return (
        <Text id={`${entity}-count-text`}>
            {totalCount} {text}
        </Text>
    );
};
