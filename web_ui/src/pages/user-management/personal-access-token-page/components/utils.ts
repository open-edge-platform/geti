// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { SortDescriptor } from 'react-stately';

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
