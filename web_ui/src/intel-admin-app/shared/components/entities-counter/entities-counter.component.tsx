// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Text } from '@geti/ui';

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
