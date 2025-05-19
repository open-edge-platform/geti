// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text } from '@geti/ui';
import { dimensionValue } from '@react-spectrum/utils';

interface UsersCountProps {
    totalMatchedCount: number;
    totalCount: number;
    hasFilters: boolean;
    id?: string;
}

export const UsersCount = ({ totalMatchedCount, totalCount, hasFilters, id }: UsersCountProps): JSX.Element => {
    return (
        <Text UNSAFE_style={{ fontSize: dimensionValue('size-130') }} data-testid={id} id={id}>
            {hasFilters ? `${totalMatchedCount} out of ${totalCount} users` : `${totalCount} users`}
        </Text>
    );
};
