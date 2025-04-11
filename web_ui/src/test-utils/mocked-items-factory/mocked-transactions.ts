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

import {
    CreditServiceName,
    Transaction,
    TransactionsAggregate,
    TransactionsAggregatesKey,
} from '../../core/credits/transactions/transactions.interface';

export const getMockedTransaction = (transaction: Partial<Transaction> = {}): Transaction => ({
    credits: 23,
    workspaceId: 'workspace_id_123',
    projectId: 'project_id_784',
    serviceName: CreditServiceName.OPTIMIZATION,
    millisecondsTimestamp: 1711312113376,
    ...transaction,
});

export const getMockedTransactionsAggregate = (
    aggregate: Partial<TransactionsAggregate> = {}
): TransactionsAggregate => ({
    group: [
        { key: TransactionsAggregatesKey.PROJECT, value: 'project_id_784' },
        { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'optimization' },
    ],
    result: {
        credits: 23,
        resources: {
            images: 23,
        },
    },
    ...aggregate,
});
