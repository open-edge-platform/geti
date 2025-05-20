// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { type SortDescriptor } from 'react-stately';

import { PartialPersonalAccessToken } from '../../../../core/personal-access-tokens/personal-access-tokens.interface';

export const sortPersonalAccessTokens = (
    tokens: PartialPersonalAccessToken[] | undefined,
    sortDescriptor: SortDescriptor | undefined,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    collator: any
) => {
    if (!sortDescriptor || !tokens) {
        return tokens;
    }

    return tokens.sort((a, b) => {
        /* @ts-expect-error Column from sort descriptor is used to get value from the current row */
        const rowA = sortDescriptor.column ? a[sortDescriptor.column] : '';
        /* @ts-expect-error Column from sort descriptor is used to get value from the current row */
        const rowB = sortDescriptor.column ? b[sortDescriptor.column] : '';

        const cmp = collator.compare(rowA, rowB);

        return sortDescriptor.direction === 'descending' ? cmp * -1 : cmp;
    });
};

export const checkIfTokenOwner = (token: PartialPersonalAccessToken, userId: string) => {
    return token.userId === userId;
};
